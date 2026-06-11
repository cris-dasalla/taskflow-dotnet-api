namespace TaskFlow.Api.Models;

/// <summary>Workflow state of a task.</summary>
public enum TaskState
{
    Todo = 0,
    InProgress = 1,
    Done = 2
}

/// <summary>Relative importance of a task.</summary>
public enum TaskPriority
{
    Low = 0,
    Medium = 1,
    High = 2
}
