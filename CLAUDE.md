# CLAUDE.md - AI Assistant Guide for lmstudio-lan-api

## Project Overview

**lmstudio-lan-api** is a LAN-based API server for LM Studio, enabling local network access to LM Studio's language model capabilities.

### Project Purpose
- Provide RESTful API access to LM Studio over local area network
- Enable multiple clients to connect to a single LM Studio instance
- Facilitate integration with various applications and tools
- Support both text generation and chat completions

## Repository Structure

This is a new repository. The recommended structure is:

```
lmstudio-lan-api/
├── src/                    # Source code
│   ├── api/               # API routes and handlers
│   ├── services/          # Business logic and LM Studio integration
│   ├── middleware/        # Express/framework middleware
│   ├── utils/             # Utility functions
│   ├── types/             # TypeScript type definitions
│   └── index.ts           # Application entry point
├── tests/                 # Test files
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures and mocks
├── docs/                  # Documentation
├── config/                # Configuration files
├── scripts/               # Build and deployment scripts
├── .env.example           # Environment variables template
├── package.json           # Node.js dependencies
├── tsconfig.json          # TypeScript configuration
└── README.md              # Project documentation
```

## Technology Stack

### Recommended Technologies
- **Runtime**: Node.js (v18+ or v20+)
- **Language**: TypeScript
- **Framework**: Express.js or Fastify
- **Testing**: Jest or Vitest
- **Linting**: ESLint with TypeScript support
- **Formatting**: Prettier
- **Documentation**: JSDoc/TSDoc

## Development Workflow

### Initial Setup
When setting up the project for the first time:

1. **Initialize Node.js project**
   ```bash
   npm init -y
   ```

2. **Install core dependencies**
   ```bash
   npm install express cors dotenv
   npm install -D typescript @types/node @types/express ts-node nodemon
   ```

3. **Configure TypeScript**
   ```bash
   npx tsc --init
   ```

4. **Set up linting and formatting**
   ```bash
   npm install -D eslint prettier eslint-config-prettier
   npx eslint --init
   ```

### Development Commands
Ensure package.json includes these scripts:

```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint . --ext .ts",
    "format": "prettier --write \"src/**/*.ts\""
  }
}
```

### Git Workflow
- **Main branch**: `main` or `master` - production-ready code
- **Feature branches**: `feature/description` - new features
- **Bug fixes**: `fix/description` - bug fixes
- **Claude branches**: `claude/claude-md-*` - AI assistant work

### Commit Conventions
Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks

## Key Architectural Decisions

### API Design
- **RESTful endpoints** following OpenAI API compatibility where possible
- **WebSocket support** for streaming responses
- **Authentication** via API keys or tokens
- **Rate limiting** to prevent abuse

### LM Studio Integration
- Connect to LM Studio's local server (typically http://localhost:1234)
- Support model switching and configuration
- Handle streaming responses
- Implement proper error handling and timeouts

### Configuration Management
- Use `.env` files for environment-specific config
- Never commit secrets or API keys
- Provide `.env.example` template
- Support configuration via environment variables

## Code Conventions

### TypeScript Standards
- **Strict mode enabled**: Use `"strict": true` in tsconfig.json
- **Explicit return types**: Always specify function return types
- **Interface over type**: Prefer `interface` for object shapes
- **No any**: Avoid `any` type; use `unknown` if necessary

### Naming Conventions
- **Files**: kebab-case (e.g., `api-client.ts`)
- **Folders**: kebab-case (e.g., `api-handlers/`)
- **Classes**: PascalCase (e.g., `LMStudioClient`)
- **Functions/Variables**: camelCase (e.g., `getModelList`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)
- **Interfaces**: PascalCase with 'I' prefix optional (e.g., `IConfig` or `Config`)

### Code Organization
```typescript
// Example structure for a service file
import { dependencies } from 'external-libs';
import { LocalModule } from './local-module';

// Constants
const MAX_RETRIES = 3;

// Types/Interfaces
interface ServiceConfig {
  endpoint: string;
  timeout: number;
}

// Class definition
export class MyService {
  private config: ServiceConfig;

  constructor(config: ServiceConfig) {
    this.config = config;
  }

  public async performAction(): Promise<void> {
    // Implementation
  }

  private helperMethod(): void {
    // Helper implementation
  }
}

// Exported functions
export function utilityFunction(): string {
  return 'result';
}
```

### Error Handling
```typescript
// Use custom error classes
export class LMStudioError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'LMStudioError';
  }
}

// Async error handling
try {
  const result = await lmStudioClient.generate(prompt);
  return result;
} catch (error) {
  if (error instanceof LMStudioError) {
    // Handle specific error
  }
  throw error;
}
```

## Testing Standards

### Test Structure
- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test API endpoints and service interactions
- **Coverage target**: Aim for >80% code coverage

### Test Naming
```typescript
describe('LMStudioClient', () => {
  describe('generate', () => {
    it('should generate text successfully with valid prompt', async () => {
      // Test implementation
    });

    it('should throw error when LM Studio is unreachable', async () => {
      // Test implementation
    });
  });
});
```

### Mocking
- Mock external dependencies (LM Studio, network calls)
- Use Jest mocks or test doubles
- Keep mocks in `tests/fixtures/` or `__mocks__/`

## API Endpoints

### Recommended Endpoints

#### Health Check
```
GET /health
Response: { status: 'ok', lmStudioConnected: boolean }
```

#### List Models
```
GET /v1/models
Response: { models: [...] }
```

#### Text Completion
```
POST /v1/completions
Body: { prompt: string, model?: string, ... }
Response: { text: string, ... }
```

#### Chat Completion
```
POST /v1/chat/completions
Body: { messages: [...], model?: string, ... }
Response: { choices: [...] }
```

#### Streaming
```
POST /v1/completions (with stream: true)
POST /v1/chat/completions (with stream: true)
Response: Server-Sent Events stream
```

## Security Considerations

### Critical Security Rules
1. **Never expose LM Studio directly to the internet** - LAN only
2. **Implement API key authentication** for production use
3. **Validate all input** to prevent injection attacks
4. **Rate limit requests** to prevent abuse
5. **Use CORS properly** to restrict client origins
6. **Keep dependencies updated** to patch vulnerabilities
7. **Never log sensitive data** (API keys, user prompts if private)

### Environment Variables
```bash
# .env.example
PORT=3000
LM_STUDIO_URL=http://localhost:1234
API_KEY=your-secret-api-key-here
CORS_ORIGIN=*
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW_MS=900000
NODE_ENV=development
```

## Dependencies Management

### Core Dependencies
- `express` - Web framework
- `cors` - CORS middleware
- `dotenv` - Environment configuration
- `axios` - HTTP client for LM Studio communication

### Development Dependencies
- `typescript` - TypeScript compiler
- `@types/node` - Node.js type definitions
- `@types/express` - Express type definitions
- `ts-node` - TypeScript execution
- `nodemon` - Development server
- `jest` - Testing framework
- `eslint` - Linting
- `prettier` - Code formatting

### Keeping Dependencies Updated
```bash
# Check for outdated packages
npm outdated

# Update packages
npm update

# Check for security vulnerabilities
npm audit
npm audit fix
```

## Performance Considerations

### Optimization Guidelines
1. **Connection pooling**: Reuse connections to LM Studio
2. **Caching**: Cache model lists and configuration
3. **Streaming**: Use streaming for long responses
4. **Timeouts**: Set appropriate timeouts for LM Studio requests
5. **Request queuing**: Queue requests if LM Studio can't handle concurrent load

### Monitoring
- Log response times
- Track error rates
- Monitor memory usage
- Track active connections

## Documentation Standards

### Code Documentation
```typescript
/**
 * Generates text completion using LM Studio
 *
 * @param prompt - The input prompt for text generation
 * @param options - Optional generation parameters
 * @returns Generated text response
 * @throws {LMStudioError} When LM Studio is unavailable or request fails
 *
 * @example
 * ```typescript
 * const result = await client.generate('Hello', { maxTokens: 100 });
 * console.log(result.text);
 * ```
 */
export async function generate(
  prompt: string,
  options?: GenerationOptions
): Promise<GenerationResult> {
  // Implementation
}
```

### README Requirements
The README.md should include:
- Project description
- Features list
- Installation instructions
- Configuration guide
- Usage examples
- API documentation
- Troubleshooting section
- Contributing guidelines

## Common Pitfalls to Avoid

### ❌ Don't Do This
```typescript
// Using 'any' type
function processData(data: any): any { }

// No error handling
const result = await fetch(url);

// Hardcoded configuration
const LM_STUDIO_URL = 'http://localhost:1234';

// Blocking operations in async code
fs.readFileSync('config.json');
```

### ✅ Do This
```typescript
// Proper typing
function processData(data: RequestData): ResponseData { }

// Error handling
try {
  const result = await fetch(url);
  if (!result.ok) throw new Error('Fetch failed');
} catch (error) {
  logger.error('Request failed', error);
  throw error;
}

// Environment-based configuration
const LM_STUDIO_URL = process.env.LM_STUDIO_URL || 'http://localhost:1234';

// Async operations
const config = await fs.promises.readFile('config.json', 'utf-8');
```

## Debugging Tips

### Common Issues
1. **LM Studio connection failed**
   - Verify LM Studio is running
   - Check the correct port (default: 1234)
   - Ensure LM Studio server is enabled

2. **TypeScript compilation errors**
   - Run `npm run build` to see detailed errors
   - Check tsconfig.json settings
   - Ensure all type definitions are installed

3. **Port already in use**
   - Change PORT in .env file
   - Kill process using the port: `lsof -ti:3000 | xargs kill`

### Logging
```typescript
// Use structured logging
import { logger } from './utils/logger';

logger.info('Server started', { port: 3000 });
logger.error('Request failed', { error, requestId });
logger.debug('Processing request', { method, path });
```

## AI Assistant Guidelines

### When Working on This Project
1. **Always check for existing patterns** before implementing new features
2. **Follow TypeScript strict mode** - no bypassing type safety
3. **Write tests** for new features and bug fixes
4. **Update documentation** when changing behavior
5. **Ask for clarification** on ambiguous requirements
6. **Security first** - validate inputs, handle errors, protect secrets
7. **Performance matters** - avoid blocking operations, use streaming

### Before Committing
- [ ] Code compiles without errors (`npm run build`)
- [ ] Tests pass (`npm test`)
- [ ] Linting passes (`npm run lint`)
- [ ] Code is formatted (`npm run format`)
- [ ] Documentation is updated
- [ ] No secrets or sensitive data in code
- [ ] Commit message follows conventions

### Communication
- Explain architectural decisions
- Highlight potential issues or trade-offs
- Suggest improvements when appropriate
- Ask questions when requirements are unclear

## Resources

### LM Studio Documentation
- LM Studio API: http://localhost:1234/docs (when running)
- OpenAI API compatibility: https://platform.openai.com/docs/api-reference

### Node.js & TypeScript
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- Node.js Best Practices: https://github.com/goldbergyoni/nodebestpractices

### Express.js
- Express Documentation: https://expressjs.com/
- Express Best Practices: https://expressjs.com/en/advanced/best-practice-performance.html

## Version History

### Latest Update
- **Date**: 2025-11-15
- **Status**: Initial CLAUDE.md creation for new repository
- **Next Steps**: Initialize project structure, set up TypeScript, implement basic API

---

**Note for AI Assistants**: This document should be updated whenever significant architectural decisions are made, new patterns are established, or the project structure changes. Keep it current and comprehensive to help future AI assistants work effectively on this codebase.
