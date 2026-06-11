namespace TaskFlow.Api.Common;

/// <summary>Base type for expected, domain-level errors that map to specific HTTP status codes.</summary>
public abstract class AppException : Exception
{
    public abstract int StatusCode { get; }
    protected AppException(string message) : base(message) { }
}

/// <summary>Requested resource does not exist (HTTP 404).</summary>
public class NotFoundException : AppException
{
    public override int StatusCode => StatusCodes.Status404NotFound;
    public NotFoundException(string message) : base(message) { }
}

/// <summary>Request conflicts with current state, e.g. duplicate email (HTTP 409).</summary>
public class ConflictException : AppException
{
    public override int StatusCode => StatusCodes.Status409Conflict;
    public ConflictException(string message) : base(message) { }
}

/// <summary>Credentials or token invalid (HTTP 401).</summary>
public class UnauthorizedException : AppException
{
    public override int StatusCode => StatusCodes.Status401Unauthorized;
    public UnauthorizedException(string message) : base(message) { }
}

/// <summary>Request is well-formed but semantically invalid (HTTP 400).</summary>
public class ValidationFailedException : AppException
{
    public override int StatusCode => StatusCodes.Status400BadRequest;
    public ValidationFailedException(string message) : base(message) { }
}
