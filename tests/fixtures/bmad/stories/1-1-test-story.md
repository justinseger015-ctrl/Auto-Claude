# Story 1.1: Test Story Title

Status: in-progress

## Story

As a **test user**,
I want to test the story parser,
so that stories are correctly parsed.

## Acceptance Criteria

1. **Given** a valid story file
   **When** the parser reads it
   **Then** the title is extracted correctly

2. **And** the acceptance criteria are parsed
   **And** preserved for display

3. **And** tasks with subtasks are captured

## Tasks / Subtasks

- [x] Task 1: Create test fixtures (AC: #1)
  - [x] Create stories directory
  - [x] Create test story file
- [ ] Task 2: Write parser tests (AC: #2)
  - [ ] Test title extraction
  - [ ] Test AC parsing
- [ ] Task 3: Test task parsing (AC: #3)

## Dev Notes

### Dependencies

- Story 2.1 - BMAD parser module structure

### Technical Details

This is a test story used for unit testing the BMAD story parser.
