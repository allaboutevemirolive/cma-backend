# src/apps/quizzes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers # Uncomment if using nested routers

from .views import QuizViewSet, QuestionViewSet, ChoiceViewSet, SubmissionViewSet

# --- Standard Router ---
router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'questions', QuestionViewSet, basename='question') # Accessible via /api/questions/
router.register(r'choices', ChoiceViewSet, basename='choice')       # Accessible via /api/choices/
router.register(r'submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
]


# --- Example Nested Router Setup (Requires pip install drf-nested-routers) ---
# from .views import QuizViewSet, QuestionViewSet, ChoiceViewSet, SubmissionViewSet
#
# router = DefaultRouter()
# router.register(r'quizzes', QuizViewSet, basename='quiz')
# router.register(r'submissions', SubmissionViewSet, basename='submission') # Top-level for submissions
#
# quizzes_router = routers.NestedDefaultRouter(router, r'quizzes', lookup='quiz')
# quizzes_router.register(r'questions', QuestionViewSet, basename='quiz-questions')
# # /api/quizzes/{quiz_pk}/questions/
#
# questions_router = routers.NestedDefaultRouter(quizzes_router, r'questions', lookup='question')
# questions_router.register(r'choices', ChoiceViewSet, basename='question-choices')
# # /api/quizzes/{quiz_pk}/questions/{question_pk}/choices/
#
# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include(quizzes_router.urls)),
#     path('', include(questions_router.urls)),
# ]
