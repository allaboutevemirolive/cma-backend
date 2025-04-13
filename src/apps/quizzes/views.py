# src/apps/quizzes/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from .models import Quiz, Question, Choice, Submission, Answer
from .serializers import (
    QuizSerializer, QuestionSerializer, ChoiceSerializer,
    SubmissionSerializer, AnswerSerializer, SubmitAnswerSerializer
)

# --- Permissions ---

class IsInstructorOrAdminReadOnly(permissions.BasePermission):
    """Allow read-only access to everyone. Write access only to instructors and admins."""

    def has_permission(self, request, view):
        return True  # Allow general access; fine-tune in has_object_permission

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True

        course_instructor = None
        if isinstance(obj, Quiz):
            course_instructor = obj.course.instructor
        elif isinstance(obj, Question):
            course_instructor = obj.quiz.course.instructor
        elif isinstance(obj, Choice):
            course_instructor = obj.question.quiz.course.instructor

        return user == course_instructor


class IsStudentOwnerOrInstructorOrAdmin(permissions.BasePermission):
    """Allows access to submission/answer owner, instructor of the quiz, or admin."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True

        if isinstance(obj, Submission):
            return user == obj.student or user == obj.quiz.course.instructor

        if isinstance(obj, Answer):
            return user == obj.submission.student or user == obj.submission.quiz.course.instructor

        return False


# --- ViewSets ---

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.select_related('course', 'course__instructor').prefetch_related('questions__choices').all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrAdminReadOnly]

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        user = self.request.user
        if not user.is_staff and user != course.instructor:
            raise PermissionDenied("Only the course instructor or admin can add a quiz.")
        serializer.save()

    @action(detail=True, methods=['post'], url_path='start-submission', permission_classes=[permissions.IsAuthenticated])
    def start_submission(self, request, pk=None):
        """Create a new 'in_progress' submission for the current user for this quiz."""
        quiz = self.get_object()
        user = request.user

        existing_submission = Submission.objects.filter(
            quiz=quiz, student=user, status=Submission.Status.IN_PROGRESS
        ).first()

        if existing_submission:
            serializer = SubmissionSerializer(existing_submission)
            return Response(serializer.data, status=status.HTTP_200_OK)

        submission = Submission.objects.create(quiz=quiz, student=user)
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related('choices').all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrAdminReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrAdminReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Handles quiz submissions.
    Disallows creation via standard POST — use start_submission on Quiz instead.
    """

    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Submission.objects.select_related('student', 'quiz__course').prefetch_related('answers').all()

        if hasattr(user, 'profile') and user.profile.role == 'instructor':
            return Submission.objects.filter(
                quiz__course__instructor=user
            ).select_related('student', 'quiz__course').prefetch_related('answers')

        return Submission.objects.filter(
            student=user
        ).select_related('student', 'quiz__course').prefetch_related('answers')

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Use the 'start-submission' action on a Quiz."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'UPDATE' not allowed. Use custom actions."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'PATCH' not allowed. Use custom actions."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method 'DELETE' not allowed."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post'], url_path='submit-answer', permission_classes=[IsStudentOwnerOrInstructorOrAdmin])
    def submit_answer(self, request, pk=None):
        """Saves or updates an answer for a specific question in a submission."""
        submission = self.get_object()
        user = request.user

        if submission.student != user:
            raise PermissionDenied("You cannot submit answers for another student.")

        if submission.status != Submission.Status.IN_PROGRESS:
            raise ValidationError("This submission is not in progress and cannot be modified.")

        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        question_id = validated_data['question_id']
        selected_choice_id = validated_data.get('selected_choice_id')
        text_answer = validated_data.get('text_answer')

        try:
            question = Question.objects.get(pk=question_id, quiz=submission.quiz)
        except Question.DoesNotExist:
            raise NotFound("Question not found or does not belong to this quiz.")

        selected_choice = None
        if selected_choice_id:
            try:
                selected_choice = Choice.objects.get(pk=selected_choice_id, question=question)
            except Choice.DoesNotExist:
                raise NotFound("Selected choice not found or does not belong to this question.")

        answer, _ = Answer.objects.update_or_create(
            submission=submission,
            question=question,
            defaults={'selected_choice': selected_choice, 'text_answer': text_answer}
        )

        return Response(AnswerSerializer(answer).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='finalize', permission_classes=[IsStudentOwnerOrInstructorOrAdmin])
    def finalize_submission(self, request, pk=None):
        """Marks the submission as completed and triggers grading."""
        submission = self.get_object()
        user = request.user

        if submission.student != user:
            raise PermissionDenied("You cannot finalize another student's submission.")

        if submission.status != Submission.Status.IN_PROGRESS:
            raise ValidationError("Submission already finalized or graded.")

        submission.finalize()  # Assume this handles grading logic
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)

