# src/apps/quizzes/serializers.py
from rest_framework import serializers
from .models import Quiz, Question, Choice, Submission, Answer
from apps.courses.serializers import CourseSerializer  # Reuse if needed (read-only)
from apps.users.serializers import UserSerializer  # Reuse if needed (read-only)
from apps.courses.models import Course  # <--- IMPORT ADDED HERE


# --- Choice Serializer ---
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "question", "text", "is_correct", "created_at", "updated_at"]
        read_only_fields = ["question"]  # Question set implicitly via URL/view usually


# --- Question Serializer ---
class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(
        many=True, read_only=True
    )  # Show choices when reading question

    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "text",
            "question_type",
            "order",
            "choices",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["quiz"]  # Quiz set implicitly via URL/view usually


# --- Quiz Serializer ---
class QuizSerializer(serializers.ModelSerializer):
    # Show questions when reading a quiz
    questions = QuestionSerializer(many=True, read_only=True)
    # Show course details (read-only)
    # Make CourseSerializer optional for Quiz list/detail if full details aren't always needed
    course = CourseSerializer(read_only=True, required=False)
    # Accept course ID for writing
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),  # Now Course is defined
        source="course",
        write_only=True,
        help_text="ID of the course this quiz belongs to.",
    )

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "course_id",
            "title",
            "description",
            "time_limit_minutes",
            "questions",
            "created_at",
            "updated_at",
        ]
        # course is already read_only=True above
        read_only_fields = ["id", "questions", "created_at", "updated_at"]


# --- Answer Serializer ---
class AnswerSerializer(serializers.ModelSerializer):
    # Optionally show question text for context
    # question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = Answer
        fields = [
            "id",
            "submission",
            "question",
            "selected_choice",
            "text_answer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["submission", "created_at", "updated_at"]  # Set by system

    def validate(self, data):
        # Basic validation example: Ensure choice belongs to the question
        question = data.get("question")
        selected_choice = data.get("selected_choice")
        if question and selected_choice:
            if selected_choice.question != question:
                raise serializers.ValidationError(
                    "Selected choice does not belong to the specified question."
                )
        # Add more validation: e.g., cannot provide both selected_choice and text_answer
        return data


# --- Submission Serializer ---
class SubmissionSerializer(serializers.ModelSerializer):
    # Show related objects (read-only)
    student = UserSerializer(read_only=True)
    # Simplified Quiz representation for submission list/detail
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)
    # quiz = QuizSerializer(read_only=True) # Use this for full quiz details
    answers = AnswerSerializer(
        many=True, read_only=True
    )  # Show answers within submission detail

    # Accept IDs for writing (usually set by view logic based on context/user)
    student_id = serializers.IntegerField(
        write_only=True, required=False
    )  # Set by view from request.user
    quiz_id = serializers.IntegerField(
        write_only=True, required=False
    )  # Set by view from URL typically

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "quiz",
            "student",
            "status",
            "status_display",
            "started_at",
            "submitted_at",
            "score",
            "answers",
            "created_at",
            "updated_at",
            "student_id",
            "quiz_id",  # Write only
        ]
        read_only_fields = [
            "id",
            "student",
            "quiz",
            "status",
            "started_at",
            "submitted_at",
            "score",
            "answers",
            "created_at",
            "updated_at",
            "status_display",
            # Status is usually managed by specific actions (finalize, grade)
        ]


# --- Serializer for submitting a single answer ---
class SubmitAnswerSerializer(serializers.Serializer):
    """Serializer specifically for the submit_answer action."""

    question_id = serializers.IntegerField(required=True)
    selected_choice_id = serializers.IntegerField(required=False, allow_null=True)
    text_answer = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    def validate(self, data):
        if data.get("selected_choice_id") is None and data.get("text_answer") is None:
            raise serializers.ValidationError(
                "Either 'selected_choice_id' or 'text_answer' must be provided."
            )
        if (
            data.get("selected_choice_id") is not None
            and data.get("text_answer") is not None
        ):
            raise serializers.ValidationError(
                "Provide either 'selected_choice_id' or 'text_answer', not both."
            )
        # Add validation to check if question_id and selected_choice_id are valid & related
        # Example: Check if choice belongs to question
        # choice_id = data.get('selected_choice_id')
        # question_id = data.get('question_id')
        # if choice_id:
        #     try:
        #         choice = Choice.objects.get(pk=choice_id)
        #         if choice.question_id != question_id:
        #             raise serializers.ValidationError("Selected choice does not belong to this question.")
        #     except Choice.DoesNotExist:
        #          raise serializers.ValidationError("Invalid choice ID.")
        return data
