"""Errors for the AI layer. Each one maps to an HTTP status code.

502 Bad Gateway          -> the AI provider failed or sent a bad answer
503 Service Unavailable  -> AI is not configured on our server
504 Gateway Timeout      -> the AI provider was too slow
"""
from app.exceptions import AppError


class AIError(AppError):
    status_code = 502
    default_message = "The AI service failed. Please try again."


class AINotConfiguredError(AIError):
    status_code = 503
    default_message = "The AI service is not configured. Set AI_PROVIDER and AI_API_KEY in the .env file."


class AITimeoutError(AIError):
    status_code = 504
    default_message = "The AI service took too long to respond. Please try again."


class AIProviderError(AIError):
    status_code = 502
    default_message = "The AI provider returned an error."


class AIInvalidResponseError(AIError):
    status_code = 502
    default_message = "The AI returned a response in an unexpected format. Please try again."
