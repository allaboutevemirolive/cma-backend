# src/apps/quizzes/admin.py
from django.contrib import admin
from .models import Quiz, Question, Choice, Submission, Answer

# --- Inlines for better management ---


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1  # Number of empty choice forms to show


class QuestionInline(admin.StackedInline):  # Or TabularInline
    model = Question
    extra = 1
    show_change_link = True  # Allow linking to the Question change page


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0  # Usually don't add answers manually here
    fields = ("question", "selected_choice", "text_answer", "created_at")
    readonly_fields = ("created_at",)
    # Can make fields readonly based on submission status if needed


# --- ModelAdmins ---


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "question_count", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "description", "course__title")
    inlines = [QuestionInline]  # Manage questions directly within the quiz

    @admin.display(description="No. Questions")
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text_summary", "quiz", "question_type", "order", "choice_count")
    list_filter = ("question_type", "quiz__course", "quiz")
    search_fields = ("text", "quiz__title")
    inlines = [ChoiceInline]  # Manage choices directly within the question

    @admin.display(description="Text")
    def text_summary(self, obj):
        return obj.text[:75] + ("..." if len(obj.text) > 75 else "")

    @admin.display(description="No. Choices")
    def choice_count(self, obj):
        return obj.choices.count()


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text_summary", "question_link", "is_correct")
    list_filter = ("is_correct", "question__quiz__course")
    search_fields = ("text", "question__text")
    autocomplete_fields = ["question"]  # Makes selecting the question easier

    @admin.display(description="Text")
    def text_summary(self, obj):
        return obj.text[:75] + ("..." if len(obj.text) > 75 else "")

    @admin.display(description="Question")
    def question_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:quizzes_question_change", args=[obj.question.id])
        return format_html('<a href="{}">{}</a>', link, obj.question)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "quiz",
        "status",
        "score",
        "started_at",
        "submitted_at",
    )
    list_filter = ("status", "quiz__course", "quiz")
    search_fields = ("student__username", "quiz__title")
    readonly_fields = ("started_at", "submitted_at", "created_at", "updated_at")
    list_select_related = ("student", "quiz")  # Optimize queries
    inlines = [AnswerInline]  # View answers within the submission


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "question",
        "selected_choice",
        "text_summary",
        "created_at",
    )
    list_filter = ("submission__quiz__course", "submission__status")
    search_fields = ("submission__student__username", "question__text", "text_answer")
    list_select_related = (
        "submission__student",
        "question",
        "selected_choice",
    )  # Optimize queries
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["submission", "question", "selected_choice"]

    @admin.display(description="Text Answer")
    def text_summary(self, obj):
        if obj.text_answer:
            return obj.text_answer[:75] + ("..." if len(obj.text_answer) > 75 else "")
        return "-"
