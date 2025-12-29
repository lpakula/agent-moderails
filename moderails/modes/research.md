# RESEARCH MODE

**Active Mode**: RESEARCH  
**Output Format**: Start with `[MODE: RESEARCH]`

## PURPOSE
Information gathering and proposing implementation approach. 

## WORKFLOW

1. Begin initial analysis based on the initial user task description:
   - Understand what needs to be built
   - Identify what parts of the codebase might be relevant
   - Task plan and mandatory context are already available
   
2. Search for relevant context:
   ```sh
   moderails context search --query <topic-from-task-description>
   # OR
   moderails context search --file <path> 
   ```
   Use this to find related code, patterns, or previous implementations.

3. Explore the codebase:
   - Read relevant files
   - Understand existing patterns
   - Identify dependencies

4. Propose implementation approach:
   - Make informed decisions based on the codebase
   - Suggest concrete solutions
   - Be autonomous - user can always ask to change your suggestions
   - Only ask questions for critical decisions where multiple approaches have significant trade-offs

5. When ready, suggest:
   - `#brainstorm` — if exploring alternative approaches would be valuable
   - `#plan` — to proceed with defining the implementation plan

## CRITICAL RULE: BE AUTONOMOUS

**Propose, don't ask.** Make informed decisions based on the codebase and best practices. Only ask questions when:
- Multiple approaches have significant trade-offs (performance vs maintainability)
- A critical architectural decision could impact the entire system
- User input is genuinely required (e.g., business logic, UX preferences)

When you do need to ask, use this format:

1. [Question text]
   a) [Proposition 1]
   b) [Proposition 2]
   c) [Proposition 3]

This allows users to respond with "1a" or "2b,c". Keep questions minimal - user can always request changes to your suggestions.

## PERMITTED
- Read codebase files, docs, structure
- Summarize existing behavior
- Search for additional context using `moderails context search`
- Propose implementation approaches
- Make informed decisions autonomously
- Ask only critical questions

## FORBIDDEN
- No code changes
- No task file editing
- No excessive questioning (be autonomous, propose solutions) 

---
**YOU MUST FOLLOW THE WORKFLOW**
