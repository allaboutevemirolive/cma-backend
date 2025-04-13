# src/apps/quizzes/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Assuming Course model is in apps.courses.models
from apps.courses.models import Course

# --- Quiz ---
class Quiz(models.Model):
    """Represents a quiz associated with a specific course."""
    course = models.ForeignKey(
        Course,
        related_name='quizzes',
        on_delete=models.CASCADE, # If course is deleted, delete its quizzes
        help_text="The course this quiz belongs to."
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Optional time limit for the quiz in minutes."
    )
    # Add other fields like pass_mark, due_date if needed

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'created_at']
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"Quiz: {self.title} for Course: {self.course.title}"

# --- Question ---
class Question(models.Model):
    """Represents a single question within a quiz."""
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
        SINGLE_CHOICE = 'SC', 'Single Choice' # Radio buttons
        TRUE_FALSE = 'TF', 'True/False'
        TEXT = 'TEXT', 'Text Answer' # Manual grading needed

    quiz = models.ForeignKey(
        Quiz,
        related_name='questions',
        on_delete=models.CASCADE # If quiz deleted, delete questions
    )
    text = models.TextField(help_text="The text of the question.")
    question_type = models.CharField(
        max_length=5,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of the question within the quiz."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['quiz', 'order', 'created_at']
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}... (Quiz: {self.quiz.title})"

# --- Choice ---
class Choice(models.Model):
    """Represents a possible answer choice for a multiple/single choice question."""
    question = models.ForeignKey(
        Question,
        related_name='choices',
        on_delete=models.CASCADE # If question deleted, delete choices
    )
    text = models.CharField(max_length=500, help_text="The text for this answer choice.")
    is_correct = models.BooleanField(
        default=False,
        help_text="Is this the correct answer choice?"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['question', 'created_at']
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    def __str__(self):
        correct_marker = " (Correct)" if self.is_correct else ""
        return f"Choice: {self.text[:50]}... for Q: {self.question.id}{correct_marker}"

# --- Submission ---
class Submission(models.Model):
    """Represents a student's attempt at completing a quiz."""
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'

    quiz = models.ForeignKey(
        Quiz,
        related_name='submissions',
        on_delete=models.CASCADE # Or PROTECT if submissions should remain after quiz deletion
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='quiz_submissions',
        on_delete=models.CASCADE # If student deleted, remove their submissions
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Calculated or manually assigned score (e.g., percentage or points)."
    )

    # Timestamps (useful for tracking grading time etc.)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        # Ensure a student has only one 'in_progress' submission per quiz
        unique_together = [['student', 'quiz', 'status']] # Note: Needs refinement if re-takes allowed
        verbose_name = "Quiz Submission"
        verbose_name_plural = "Quiz Submissions"

    def __str__(self):
        return f"Submission by {self.student.username} for {self.quiz.title} ({self.get_status_display()})"

    def finalize(self):
        """Marks the submission as completed and calculates score (basic example)."""
        if self.status == Status.IN_PROGRESS:
            self.status = Status.SUBMITTED
            self.submitted_at = timezone.now()
            self.calculate_score() # Call score calculation logic
            self.save()

    def calculate_score(self):
        """Basic auto-grading for multiple/single choice questions."""
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            self.score = 0.00
            self.status = Status.GRADED # Mark as graded even if score is 0
            return

        correct_answers = 0
        # Get all answers for this submission eagerly
        answers = self.answers.select_related('question', 'selected_choice').all()
        answer_map = {ans.question_id: ans for ans in answers}

        for question in self.quiz.questions.all():
            # Only grade choice-based questions automatically here
            if question.question_type in [Question.QuestionType.MULTIPLE_CHOICE,
                                          Question.QuestionType.SINGLE_CHOICE,
                                          Question.QuestionType.TRUE_FALSE]:
                student_answer = answer_map.get(question.id)
                if student_answer and student_answer.selected_choice and student_answer.selected_choice.is_correct:
                    correct_answers += 1
            # Add logic for grading TEXT type if needed (would likely require manual intervention)

        self.score = (correct_answers / total_questions) * 100.00
        self.status = Status.GRADED # Mark as graded after calculation
        # Consider rounding score


# --- Answer ---
class Answer(models.Model):
    """Represents a student's answer to a single question within a submission."""
    submission = models.ForeignKey(
        Submission,
        related_name='answers',
        on_delete=models.CASCADE # If submission deleted, delete answers
    )
    question = models.ForeignKey(
        Question,
        related_name='answers',
        on_delete=models.CASCADE # If question deleted, delete answers
    )
    # For MC/SC/TF questions:
    selected_choice = models.ForeignKey(
        Choice,
        related_name='answers',
        on_delete=models.SET_NULL, # Keep answer record even if choice deleted, just mark null
        null=True, blank=True
    )
    # For TEXT questions:
    text_answer = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A student should only have one answer per question per submission
        unique_together = [['submission', 'question']]
        ordering = ['submission', 'question__order']
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self):
        if self.selected_choice:
            answer_text = f"Choice: {self.selected_choice.id}"
        elif self.text_answer:
            answer_text = f"Text: {self.text_answer[:20]}..."
        else:
            answer_text = "No Answer"
        return f"Answer for Q:{self.question.id} in Sub:{self.submission.id} - {answer_text}"
