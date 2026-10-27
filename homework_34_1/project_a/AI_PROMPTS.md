# AI Prompts

## Code Review

### 1. Checkout view

Review the Django checkout view from my BookStore project.

Focus on:
- code quality;
- readability;
- transaction handling;
- Stripe integration;
- unnecessary code duplication;
- possible improvements.

Suggest only valid and necessary changes without introducing
unnecessary architectural changes.

### 2. Checkout success view

Review the Django checkout_success view from my BookStore project.

Focus specifically on:
- database transactions;
- concurrent requests;
- order status updates;
- stock consistency;
- preventing duplicate payment processing.

Suggest only valid and necessary changes.

### 3. Async book list view

Review the async_book_list Django view from my BookStore project.

Focus on:
- asynchronous database access;
- correct Django async ORM usage;
- readability;
- unnecessary operations.

Suggest only valid and necessary changes.

## Test Generation

Generate pytest-django tests for 2-3 models from my Django
BookStore project.

Use the existing factory-boy factories:
- CategoryFactory
- BookFactory
- OrderFactory

Every generated test must contain the comment:

Generated with AI, reviewed and modified

The tests should verify model behavior and should not duplicate
the existing test suite unnecessarily.

## Documentation

Generate concise Python docstrings for all class-based and
function-based views in store/views.py.

The docstrings should describe the purpose of each view in one
short sentence.

## README

Update the README of the Django BookStore project with an
"AI Usage" section.

The section should describe:
- AI code review;
- AI-generated tests;
- AI-generated documentation;
- the prompts used during the task.