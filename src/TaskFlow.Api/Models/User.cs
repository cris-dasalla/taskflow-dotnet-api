namespace TaskFlow.Api.Models;

/// <summary>
/// An application user who can authenticate and own/assign tasks.
/// </summary>
public class User
{
    public int Id { get; set; }

    public string Email { get; set; } = string.Empty;

    public string DisplayName { get; set; } = string.Empty;

    /// <summary>Hashed password. Never store or return the plain-text value.</summary>
    public string PasswordHash { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    /// <summary>Tasks created by this user.</summary>
    public ICollection<TaskItem> CreatedTasks { get; set; } = new List<TaskItem>();

    /// <summary>Tasks assigned to this user.</summary>
    public ICollection<TaskItem> AssignedTasks { get; set; } = new List<TaskItem>();
}
