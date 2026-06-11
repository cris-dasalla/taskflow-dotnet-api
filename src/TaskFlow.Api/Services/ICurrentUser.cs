namespace TaskFlow.Api.Services;

/// <summary>Exposes the id of the authenticated user for the current request.</summary>
public interface ICurrentUser
{
    int Id { get; }
}
