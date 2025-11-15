# CLAUDE_TYPESCRIPT.md - AI Assistant Guide for lmstudio-lan-api-typescript

## Project Overview

**lmstudio-lan-api-typescript** (also known as **LM Studio LAN Gateway - TypeScript Edition**) is a production-ready LAN-based API gateway for LM Studio, enabling secure local network access to LM Studio's language model capabilities.

### Project Purpose
- Provide a secure gateway between LAN clients and LM Studio's OpenAI-compatible API
- Enable remote model management via admin endpoints (load, unload, activate models)
- Support load-time parameters (context length, GPU offload, TTL)
- Add security features: API key authentication, IP allow-listing
- Transparently proxy all `/v1/...` requests to LM Studio's local API
- Provide real-time debugging with Server-Sent Events (SSE)
- Structured logging and clean resource management

### Key Features
- **Admin API**: Load models with custom configurations, unload models, activate defaults
- **Transparent Proxy**: Forward all `/v1/*` endpoints (chat, completions, etc.) to LM Studio
- **Security**: API key authentication and IP/CIDR-based access control
- **Real-time Debugging**: SSE endpoints for live model loading progress and inference monitoring
- **Production-Ready**: Proper error handling, logging, startup/shutdown lifecycle

## Repository Structure

```
lmstudio-lan-api-typescript/
├── src/
│   ├── config/
│   │   ├── settings.ts           # Zod-based configuration and validation
│   │   └── logger.ts             # Winston logger configuration
│   ├── middleware/
│   │   ├── ipAllowlist.ts        # IP/CIDR allowlist middleware
│   │   └── apiKey.ts             # API key authentication middleware
│   ├── types/
│   │   └── models.ts             # Zod schemas and TypeScript types
│   ├── routes/
│   │   ├── admin.ts              # /admin router for model management
│   │   ├── debug.ts              # /debug router for real-time debugging
│   │   └── proxy.ts              # /v1 proxy router
│   ├── utils/
│   │   └── eventBroadcaster.ts   # SSE event broadcasting utilities
│   └── index.ts                  # Express app assembly and server startup
├── tests/
│   ├── unit/                     # Unit tests
│   │   ├── middleware/           # Middleware tests
│   │   ├── routes/               # Route handler tests
│   │   └── utils/                # Utility function tests
│   ├── integration/              # Integration tests
│   │   ├── admin.test.ts         # Admin API integration tests
│   │   ├── debug.test.ts         # Debug API integration tests
│   │   └── proxy.test.ts         # Proxy integration tests
│   └── fixtures/                 # Test fixtures and mocks
│       ├── mockModels.ts         # Mock model data
│       └── mockLMStudio.ts       # Mock LM Studio responses
├── dist/                         # Compiled JavaScript (gitignored)
├── node_modules/                 # Dependencies (gitignored)
├── .env.example                  # Environment variables template
├── .gitignore
├── .eslintrc.json                # ESLint configuration
├── .prettierrc                   # Prettier configuration
├── tsconfig.json                 # TypeScript compiler configuration
├── jest.config.js                # Jest testing configuration
├── package.json                  # NPM dependencies and scripts
├── package-lock.json
├── Dockerfile                    # Docker container definition
├── docker-compose.yml            # Docker Compose setup
└── README.md                     # Project documentation
```

## Technology Stack

### Core Technologies
- **Language**: TypeScript 5.3+
- **Runtime**: Node.js 20+ (LTS)
- **Framework**: Express.js 4.x
- **HTTP Client**: axios (with streaming support)
- **Validation**: Zod (schema validation and type inference)
- **Logging**: Winston (structured logging)
- **SSE**: Built-in with Express Response streaming

### Development Tools
- **Linting**: ESLint with TypeScript plugins
- **Code Formatting**: Prettier
- **Type Checking**: TypeScript compiler (tsc)
- **Testing**: Jest + Supertest
- **Dev Server**: tsx (TypeScript execution with watch mode)
- **Build**: tsc (TypeScript compiler)

### Security & Middleware
- **Security Headers**: helmet
- **CORS**: cors middleware
- **IP Validation**: ipaddr.js (CIDR range support)

## Development Workflow

### Initial Setup

1. **Initialize Node.js project**
   ```bash
   mkdir lmstudio-lan-api-typescript
   cd lmstudio-lan-api-typescript
   npm init -y
   ```

2. **Install dependencies**
   ```bash
   # Core dependencies
   npm install express cors helmet winston axios zod dotenv ipaddr.js

   # TypeScript and dev dependencies
   npm install -D typescript @types/node @types/express @types/cors \
     tsx eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin \
     prettier eslint-config-prettier eslint-plugin-prettier \
     jest @types/jest ts-jest supertest @types/supertest
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize TypeScript configuration**
   ```bash
   npx tsc --init
   # Then edit tsconfig.json with project settings
   ```

### Development Commands

**Run the server:**
```bash
# Development mode with auto-reload
npm run dev

# Or manually
npx tsx watch src/index.ts

# Production mode (compiled)
npm run build
npm start
```

**Testing:**
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- tests/unit/middleware/apiKey.test.ts

# Run integration tests only
npm test -- tests/integration/
```

**Code Quality:**
```bash
# Lint code
npm run lint

# Fix lint errors
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check

# Run all checks
npm run check
```

**Build:**
```bash
# Compile TypeScript
npm run build

# Clean build artifacts
npm run clean
```

### Git Workflow
- **Main branch**: `main` - production-ready code
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
- `perf:` - Performance improvements
- `security:` - Security fixes

## Key Architectural Decisions

### 1. Gateway Pattern
- **Separation of Concerns**: Gateway handles security, routing, and coordination; LM Studio handles model inference
- **LM Studio Assumption**: Runs on same machine at `http://127.0.0.1:1234` (configurable)
- **No Direct Model Management**: Uses LM Studio's API (no Python SDK in TypeScript version)

### 2. API Design

#### Admin Endpoints (`/admin`)
- `GET /admin/models` - List available models
- `POST /admin/models/load` - Load model with configuration
- `POST /admin/models/unload` - Unload model
- `POST /admin/models/activate` - Set active default model

#### Debug Endpoints (`/debug`)
- `GET /debug/stream` - Server-Sent Events stream for real-time debug info
- `GET /debug/status` - Current status snapshot (loading/inference state)
- `GET /debug/metrics` - Performance metrics (tokens/sec, memory usage, etc.)

#### Proxy Endpoints (`/v1/*`)
- All OpenAI-compatible endpoints: `/v1/chat/completions`, `/v1/completions`, etc.
- Automatically inject active model and default inference params if missing
- Transparent pass-through to LM Studio

#### Health Check
- `GET /health` - Simple health check (optionally bypass auth)

### 3. Security Architecture

**API Key Authentication:**
- Header-based: `X-API-Key: your-secret-key`
- Configurable via `GATEWAY_API_KEY` env var
- Disabled if env var is empty (NOT recommended for production)

**IP Allow-listing:**
- Support for single IPs, CIDR ranges, or wildcard `*`
- Examples: `192.168.0.0/24`, `10.0.0.2,10.0.0.3`
- Configured via `IP_ALLOWLIST` env var
- Uses ipaddr.js for CIDR validation

**Middleware Order:**
1. Helmet (security headers)
2. CORS middleware
3. Body parsing (express.json, express.urlencoded)
4. IP allowlist check
5. API key validation
6. Route handlers
7. 404 handler
8. Error handler

### 4. Model Management

**LM Studio HTTP API:**
- Use axios for HTTP requests to LM Studio API
- Support for load config: context length, GPU settings, etc.
- TTL (time-to-live) for automatic unloading
- Multiple model instances via `instance_id`

**Active Model State:**
- Gateway maintains current "active" model in Express app locals
- Auto-inject active model into `/v1` requests if `model` field is missing
- Apply default inference parameters (temperature, max_tokens, etc.)

### 5. Application State Management

**Express App State Pattern:**
```typescript
interface AppState {
  activeModel: {
    modelKey: string | null;
    instanceId: string | null;
    defaultInference: Record<string, any>;
  };
  debugState: {
    status: 'idle' | 'loading_model' | 'processing_inference' | 'error';
    currentOperation: OperationInfo | null;
    recentRequests: RequestInfo[];
    totalRequests: number;
    totalErrors: number;
  };
}

// Attach to Express app
app.locals.appState = appState;

// Access in route handlers
const appState = req.app.locals.appState as AppState;
```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# LM Studio API URL (typically localhost)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# Gateway bind settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Security: API key (REQUIRED for production)
GATEWAY_API_KEY=change-me-please

# Security: IP allow-list
# Examples:
#   "*" - allow all (dev only)
#   "192.168.0.0/24" - allow subnet
#   "10.0.0.2,10.0.0.3" - specific IPs
IP_ALLOWLIST=192.168.0.0/24,10.0.0.0/24

# Allow unauthenticated /health checks
REQUIRE_AUTH_FOR_HEALTH=false

# Logging level (error, warn, info, debug)
LOG_LEVEL=info

# Node environment
NODE_ENV=development
```

### Settings Implementation Pattern

**Always use Zod for validation:**
```typescript
import { z } from 'zod';
import dotenv from 'dotenv';

dotenv.config();

const envSchema = z.object({
  LMSTUDIO_BASE_URL: z.string().url().default('http://127.0.0.1:1234'),
  GATEWAY_HOST: z.string().default('0.0.0.0'),
  GATEWAY_PORT: z.coerce.number().int().min(1).max(65535).default(8001),
  GATEWAY_API_KEY: z.string().default(''),
  IP_ALLOWLIST: z.string().default('*'),
  REQUIRE_AUTH_FOR_HEALTH: z
    .enum(['true', 'false'])
    .transform((val) => val === 'true')
    .default('false'),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

const env = envSchema.parse(process.env);

export const settings = {
  lmStudioBaseUrl: env.LMSTUDIO_BASE_URL,
  gatewayHost: env.GATEWAY_HOST,
  gatewayPort: env.GATEWAY_PORT,
  gatewayApiKey: env.GATEWAY_API_KEY,
  ipAllowlist: env.IP_ALLOWLIST,
  requireAuthForHealth: env.REQUIRE_AUTH_FOR_HEALTH,
  logLevel: env.LOG_LEVEL,
  nodeEnv: env.NODE_ENV,

  // Computed properties
  get ipAllowlistItems(): string[] {
    return this.ipAllowlist
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  },

  get apiKeyEnabled(): boolean {
    return this.gatewayApiKey.length > 0;
  },
};
```

## Code Conventions

### TypeScript Style Guide

**Follow TypeScript best practices:**
- Line length: 100 characters (Prettier default: 80)
- Indentation: 2 spaces
- Semicolons: Required
- Quotes: Single quotes for strings
- Imports: Group by external → internal, separated by blank lines
- Use strict mode (`"strict": true` in tsconfig.json)

### Naming Conventions

- **Files/Modules**: `camelCase.ts` (e.g., `ipAllowlist.ts`, `apiKey.ts`)
- **Classes**: `PascalCase` (e.g., `EventBroadcaster`, `HttpError`)
- **Interfaces/Types**: `PascalCase` (e.g., `LoadModelRequest`, `AppState`)
- **Functions**: `camelCase` (e.g., `loadModel`, `broadcastEvent`)
- **Variables**: `camelCase` (e.g., `activeModel`, `httpClient`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: `_leadingUnderscore` (e.g., `_validateIp`)
- **Type parameters**: Single uppercase letter or `PascalCase` (e.g., `T`, `TRequest`)

### Type Definitions

**Always use explicit types:**
```typescript
import { Request, Response, NextFunction, Router } from 'express';
import { z } from 'zod';

// Zod schema for runtime validation
const LoadModelRequestSchema = z.object({
  modelKey: z.string().min(1),
  instanceId: z.string().optional(),
  loadConfig: z.record(z.any()).optional(),
  ttlSeconds: z.number().int().nonnegative().optional(),
  defaultInference: z.record(z.any()).optional(),
  activate: z.boolean().default(true),
});

// TypeScript type inferred from Zod schema
type LoadModelRequest = z.infer<typeof LoadModelRequestSchema>;

// Route handler with explicit types
async function loadModel(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    // Validate request body
    const payload = LoadModelRequestSchema.parse(req.body);

    // Process...
    const result = await processModelLoad(payload);

    res.json(result);
  } catch (error) {
    next(error);
  }
}
```

### Error Handling

**Use custom error classes and middleware:**
```typescript
// Custom error class
class HttpError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

// Usage in route handlers
if (!modelKey) {
  throw new HttpError(400, 'model_key is required');
}

// Try-catch for external services
try {
  const response = await axios.get(`${settings.lmStudioBaseUrl}/v0/models`);
  return response.data;
} catch (error) {
  if (axios.isAxiosError(error)) {
    logger.error('Error connecting to LM Studio:', error.message);
    throw new HttpError(503, 'LM Studio API unreachable', {
      originalError: error.message,
    });
  }
  throw error;
}

// Global error handler middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof HttpError) {
    logger.warn(`HTTP ${err.statusCode}: ${err.message}`, {
      path: req.path,
      details: err.details,
    });
    res.status(err.statusCode).json({
      error: err.message,
      ...(err.details && { details: err.details }),
    });
  } else if (err instanceof z.ZodError) {
    logger.warn('Validation error:', err.errors);
    res.status(400).json({
      error: 'Validation failed',
      details: err.errors,
    });
  } else {
    logger.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### Logging Pattern

**Use Winston with structured logging:**
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: settings.logLevel,
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
          const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
          return `${timestamp} [${level}]: ${message} ${metaStr}`;
        })
      ),
    }),
  ],
});

// Usage
logger.info('Server started', {
  port: settings.gatewayPort,
  host: settings.gatewayHost,
});

logger.warn('Forbidden IP attempted access', {
  ip: clientIp,
  path: req.path,
});

logger.error('Failed to load model', {
  modelKey,
  error: err.message,
  stack: err.stack,
});
```

### Middleware Pattern

**Use Express middleware with proper typing:**
```typescript
import { Request, Response, NextFunction } from 'express';

export function apiKeyMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Skip if API key is not enabled
  if (!settings.apiKeyEnabled) {
    return next();
  }

  // Skip for health check if configured
  if (req.path === '/health' && !settings.requireAuthForHealth) {
    return next();
  }

  // Validate API key
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || apiKey !== settings.gatewayApiKey) {
    logger.warn('Unauthorized request', {
      ip: req.ip,
      path: req.path,
      hasKey: !!apiKey,
    });
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }

  next();
}
```

### Server-Sent Events (SSE) Pattern

**Implement SSE for real-time debugging:**
```typescript
import { Request, Response } from 'express';
import { EventEmitter } from 'events';

// Global event emitter for broadcasting
const debugEventEmitter = new EventEmitter();
debugEventEmitter.setMaxListeners(100); // Support many concurrent clients

// Broadcast helper function
export function broadcastDebugEvent(
  eventType: string,
  data: Record<string, any>
): void {
  const event = {
    type: eventType,
    data: {
      ...data,
      timestamp: new Date().toISOString(),
    },
  };
  debugEventEmitter.emit('debug-event', event);
}

// SSE endpoint
router.get('/stream', (req: Request, res: Response): void => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

  // Send initial connection event
  res.write(
    `event: connected\ndata: ${JSON.stringify({
      timestamp: new Date().toISOString(),
      message: 'Debug stream connected',
    })}\n\n`
  );

  // Event listener
  const eventListener = (event: { type: string; data: any }) => {
    res.write(`event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`);
  };

  debugEventEmitter.on('debug-event', eventListener);

  // Cleanup on client disconnect
  req.on('close', () => {
    debugEventEmitter.off('debug-event', eventListener);
    logger.debug('Client disconnected from debug stream', { ip: req.ip });
  });

  // Keep-alive ping every 30 seconds
  const keepAliveInterval = setInterval(() => {
    res.write(': keep-alive\n\n');
  }, 30000);

  req.on('close', () => {
    clearInterval(keepAliveInterval);
  });
});
```

### Zod Validation Pattern

**Define schemas for all request/response types:**
```typescript
import { z } from 'zod';

// Load configuration schema
const LoadConfigSchema = z.object({
  contextLength: z.number().int().positive().optional(),
  gpu: z
    .object({
      ratio: z.number().min(0).max(1).optional(),
      layers: z.number().int().nonnegative().optional(),
    })
    .optional(),
  cpuThreads: z.number().int().positive().optional(),
  ropeFrequencyBase: z.number().positive().optional(),
  ropeFrequencyScale: z.number().positive().optional(),
});

// Default inference parameters schema
const DefaultInferenceSchema = z.object({
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().int().positive().optional(),
  topP: z.number().min(0).max(1).optional(),
  topK: z.number().int().nonnegative().optional(),
  repeatPenalty: z.number().min(0).optional(),
  stopStrings: z.array(z.string()).optional(),
  stream: z.boolean().optional(),
});

// Load model request schema
export const LoadModelRequestSchema = z.object({
  modelKey: z.string().min(1, 'modelKey is required'),
  instanceId: z.string().optional(),
  loadConfig: LoadConfigSchema.optional(),
  ttlSeconds: z.number().int().nonnegative().optional(),
  defaultInference: DefaultInferenceSchema.optional(),
  activate: z.boolean().default(true),
});

// Infer TypeScript types from schemas
export type LoadConfig = z.infer<typeof LoadConfigSchema>;
export type DefaultInference = z.infer<typeof DefaultInferenceSchema>;
export type LoadModelRequest = z.infer<typeof LoadModelRequestSchema>;

// Usage in route handler
router.post('/models/load', async (req, res, next) => {
  try {
    // Validate and parse
    const payload = LoadModelRequestSchema.parse(req.body);

    // TypeScript now knows the exact type of payload
    const result = await loadModelHandler(payload);

    res.json(result);
  } catch (error) {
    next(error); // Zod errors handled by error middleware
  }
});
```

## Testing Standards

### Test Structure

**Use Jest with Supertest:**
```typescript
import request from 'supertest';
import { Express } from 'express';
import { createApp } from '../src/index';

describe('Admin API', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  describe('GET /admin/models', () => {
    it('should return list of models', async () => {
      const response = await request(app)
        .get('/admin/models')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('models');
      expect(Array.isArray(response.body.models)).toBe(true);
    });

    it('should return 401 without API key', async () => {
      const response = await request(app).get('/admin/models');

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('POST /admin/models/load', () => {
    it('should load model with valid request', async () => {
      const payload = {
        modelKey: 'test-model',
        activate: true,
      };

      const response = await request(app)
        .post('/admin/models/load')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '')
        .send(payload);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status');
      expect(response.body.status).toBe('loaded');
    });

    it('should return 400 with invalid request', async () => {
      const payload = {
        // Missing modelKey
        activate: true,
      };

      const response = await request(app)
        .post('/admin/models/load')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '')
        .send(payload);

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('error');
    });
  });
});
```

### Test Naming Convention

```typescript
describe('<Component/Route>', () => {
  describe('<Method/Function>', () => {
    it('should <expected behavior> when <condition>', () => {
      // Test implementation
    });
  });
});

// Examples:
describe('API Key Middleware', () => {
  describe('apiKeyMiddleware', () => {
    it('should allow request with valid API key', () => { /* ... */ });
    it('should reject request with invalid API key', () => { /* ... */ });
    it('should skip validation when API key is disabled', () => { /* ... */ });
  });
});

describe('IP Allowlist Middleware', () => {
  describe('ipAllowlistMiddleware', () => {
    it('should allow IP in CIDR range', () => { /* ... */ });
    it('should block IP outside CIDR range', () => { /* ... */ });
    it('should allow all IPs with wildcard', () => { /* ... */ });
  });
});
```

### Mocking

**Mock external dependencies with Jest:**
```typescript
import axios from 'axios';
import { jest } from '@jest/globals';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Model Loading', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle LM Studio API success', async () => {
    // Mock axios response
    mockedAxios.get.mockResolvedValue({
      data: { models: ['model1', 'model2'] },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {},
    });

    const result = await listModels();

    expect(result.models).toHaveLength(2);
    expect(mockedAxios.get).toHaveBeenCalledWith(
      'http://127.0.0.1:1234/v0/models'
    );
  });

  it('should handle LM Studio API failure', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Connection refused'));

    await expect(listModels()).rejects.toThrow('LM Studio API unreachable');
  });
});
```

### Coverage Target

- **Minimum**: 80% overall coverage
- **Critical paths**: 95%+ (authentication, proxy logic, model management)
- **Utilities**: 90%+

**Coverage configuration in package.json:**
```json
{
  "jest": {
    "collectCoverageFrom": [
      "src/**/*.ts",
      "!src/**/*.d.ts",
      "!src/index.ts"
    ],
    "coverageThreshold": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

## API Endpoints Reference

### Admin API

#### List Models
```http
GET /admin/models
Headers:
  X-API-Key: your-secret-key

Response: 200 OK
{
  "models": [
    {"name": "qwen2.5-7b-instruct", ...},
    ...
  ]
}
```

#### Load Model
```http
POST /admin/models/load
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "modelKey": "qwen2.5-7b-instruct",
  "instanceId": "primary-qwen",
  "loadConfig": {
    "contextLength": 8192,
    "gpu": {"ratio": 1.0}
  },
  "ttlSeconds": 3600,
  "defaultInference": {
    "temperature": 0.4,
    "maxTokens": 2048
  },
  "activate": true
}

Response: 200 OK
{
  "status": "loaded",
  "modelKey": "qwen2.5-7b-instruct",
  "instanceId": "primary-qwen",
  "activated": true
}
```

#### Unload Model
```http
POST /admin/models/unload
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "modelKey": "qwen2.5-7b-instruct",
  "instanceId": null
}

Response: 200 OK
{
  "status": "unloaded",
  "modelKey": "qwen2.5-7b-instruct"
}
```

#### Activate Model
```http
POST /admin/models/activate
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "modelKey": "qwen2.5-7b-instruct",
  "instanceId": "primary-qwen",
  "defaultInference": {
    "temperature": 0.3
  }
}

Response: 200 OK
{
  "status": "activated",
  "modelKey": "qwen2.5-7b-instruct"
}
```

### Proxy API (OpenAI-compatible)

All `/v1/*` endpoints are proxied to LM Studio with automatic model injection:

```http
POST /v1/chat/completions
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
  // "model" is auto-injected from active model if missing
  // default inference params are auto-injected if missing
}
```

### Debug API (Real-time Monitoring)

#### Stream Debug Events (SSE)
```http
GET /debug/stream
Headers:
  X-API-Key: your-secret-key
  Accept: text/event-stream

Response: Server-Sent Events stream
event: connected
data: {"timestamp": "2025-11-15T10:30:00Z", "message": "Debug stream connected"}

event: model_load_start
data: {"modelKey": "qwen2.5-7b-instruct", "timestamp": "2025-11-15T10:30:00Z"}

event: model_load_progress
data: {"progress": 0.25, "stage": "loading_weights"}

event: model_load_complete
data: {"modelKey": "qwen2.5-7b-instruct", "totalTimeMs": 5432}

event: inference_start
data: {"requestId": "abc123", "promptTokens": 45}

event: inference_complete
data: {"requestId": "abc123", "totalTokens": 120, "totalTimeMs": 7890}
```

#### Get Current Status
```http
GET /debug/status
Headers:
  X-API-Key: your-secret-key

Response: 200 OK
{
  "status": "idle",
  "currentOperation": null,
  "activeModel": {
    "modelKey": "qwen2.5-7b-instruct",
    "instanceId": "primary-qwen"
  },
  "recentRequests": []
}
```

#### Get Performance Metrics
```http
GET /debug/metrics
Headers:
  X-API-Key: your-secret-key

Response: 200 OK
{
  "modelInfo": {
    "modelKey": "qwen2.5-7b-instruct",
    "contextLength": 8192
  },
  "performance": {
    "avgTokensPerSec": 15.2,
    "totalRequests": 45
  },
  "errors": {
    "totalErrors": 2
  }
}
```

## Security Best Practices

### Critical Security Rules

1. **ALWAYS set `GATEWAY_API_KEY` in production** - never run without authentication
2. **Use IP allow-listing** - restrict to known LAN subnets
3. **Never expose to public internet** - LAN only, use VPN if remote access needed
4. **Keep secrets in environment variables** - never commit to git
5. **Use HTTPS in production** - terminate SSL at reverse proxy (nginx/Traefik)
6. **Rotate API keys regularly** - use secrets management
7. **Validate all inputs** - Zod schemas handle this automatically
8. **Log security events** - unauthorized access attempts, IP blocks
9. **Keep dependencies updated** - run `npm outdated` regularly
10. **Never log sensitive data** - API keys, user prompts (if private)

### .gitignore Essential Entries

```gitignore
# Environment
.env
.env.local
.env.*.local

# Node
node_modules/
npm-debug.log
yarn-error.log

# Build
dist/
build/
*.tsbuildinfo

# Testing
coverage/
.jest/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log
```

## Dependencies Management

### Core Dependencies

```json
{
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "winston": "^3.11.0",
    "axios": "^1.6.2",
    "zod": "^3.22.4",
    "dotenv": "^16.3.1",
    "ipaddr.js": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/node": "^20.10.6",
    "@types/express": "^4.17.21",
    "@types/cors": "^2.8.17",
    "tsx": "^4.7.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/parser": "^6.18.0",
    "@typescript-eslint/eslint-plugin": "^6.18.0",
    "prettier": "^3.1.1",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-prettier": "^5.1.2",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.11",
    "ts-jest": "^29.1.1",
    "supertest": "^6.3.3",
    "@types/supertest": "^6.0.2"
  }
}
```

### Keeping Dependencies Updated

```bash
# Check for outdated packages
npm outdated

# Update all packages (with caution)
npm update

# Check for security vulnerabilities
npm audit

# Fix security vulnerabilities
npm audit fix
```

## Performance Considerations

### Optimization Guidelines

1. **Async all the way**: Use `async/await` for all I/O operations
2. **Connection reuse**: Single axios instance for all LM Studio requests
3. **Streaming support**: Proxy streaming responses from LM Studio as-is
4. **Request timeout**: Set appropriate timeouts (default: 60s, configurable)
5. **Clustering**: Use PM2 or Node.js cluster module for multi-core usage
6. **Compression**: Enable gzip compression for responses
7. **Caching**: Cache model list if it doesn't change frequently

### Monitoring & Observability

**Structured Logging:**
```typescript
logger.info('Request processed', {
  endpoint: req.path,
  method: req.method,
  clientIp: req.ip,
  responseTimeMs: elapsed,
  statusCode: res.statusCode,
});
```

**Future Enhancements:**
- Prometheus metrics via `prom-client`
- Distributed tracing (OpenTelemetry)
- Health check improvements (check LM Studio connectivity)

## Docker Deployment

### Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Production stage
FROM node:20-alpine

ENV NODE_ENV=production

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8001/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Run the application
CMD ["node", "dist/index.js"]
```

### docker-compose.yml

```yaml
version: '3.9'

services:
  lmstudio-gateway:
    build: .
    container_name: lmstudio-lan-gateway-ts
    ports:
      - '${GATEWAY_PORT:-8001}:8001'
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test:
        [
          'CMD',
          'node',
          '-e',
          "require('http').get('http://localhost:8001/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

## Common Pitfalls to Avoid

### ❌ Don't Do This

```typescript
// Using synchronous blocking calls
import fs from 'fs'; // DON'T use synchronous methods
const data = fs.readFileSync('file.txt'); // Blocks the event loop!

// Missing type annotations
function processData(data) {  // No types!
  return data;
}

// Bare any types
function process(data: any): any {  // Too broad!
  return data;
}

// Ignoring errors
try {
  await doSomething();
} catch (err) {
  // Silent failure - BAD!
}

// Hardcoded secrets
const API_KEY = "my-secret-key";  // NEVER!

// Missing validation
app.post('/endpoint', async (req, res) => {
  const data = req.body;  // No validation!
  // Process data...
});
```

### ✅ Do This

```typescript
// Async file operations
import { promises as fs } from 'fs';
const data = await fs.readFile('file.txt', 'utf-8');

// Proper type annotations
function processData(data: RequestData): ProcessedData {
  return new ProcessedData(data);
}

// Specific types
function process(data: RequestData): ResponseData {
  return transform(data);
}

// Proper error handling
try {
  await doSomething();
} catch (err) {
  logger.error('Failed to do something:', err);
  throw new HttpError(500, 'Operation failed');
}

// Environment-based secrets
import { settings } from './config/settings';
const apiKey = settings.gatewayApiKey;

// Zod validation
const RequestSchema = z.object({ /* ... */ });
app.post('/endpoint', async (req, res, next) => {
  try {
    const data = RequestSchema.parse(req.body);
    // Process validated data...
  } catch (error) {
    next(error);
  }
});
```

## Debugging Tips

### Common Issues

1. **LM Studio connection failed**
   ```
   Error: ECONNREFUSED / Service unavailable

   Solutions:
   - Verify LM Studio is running
   - Check LMSTUDIO_BASE_URL in .env (default: http://127.0.0.1:1234)
   - Ensure LM Studio API server is enabled
   - Test manually: curl http://127.0.0.1:1234/v1/models
   ```

2. **401 Unauthorized**
   ```
   Error: Unauthorized

   Solutions:
   - Check X-API-Key header matches GATEWAY_API_KEY in .env
   - Verify .env file is loaded (check settings object)
   - For /health, check REQUIRE_AUTH_FOR_HEALTH setting
   ```

3. **403 Forbidden**
   ```
   Error: Forbidden

   Solutions:
   - Check client IP is in IP_ALLOWLIST
   - Verify CIDR notation is correct (e.g., 192.168.0.0/24)
   - Try IP_ALLOWLIST=* for testing (NOT for production)
   ```

4. **TypeScript compilation errors**
   ```
   Error: Cannot find module or type declaration

   Solutions:
   - Ensure all @types/* packages are installed
   - Check tsconfig.json paths and includes
   - Run npm install to ensure all deps are installed
   - Clear build cache: rm -rf dist && npm run build
   ```

5. **Port already in use**
   ```
   Error: EADDRINUSE

   Solutions:
   - Check if another process is using port 8001
   - Use different port: GATEWAY_PORT=8002 npm run dev
   - Kill existing process: lsof -ti:8001 | xargs kill
   ```

### Logging for Debugging

```bash
# Enable DEBUG level logging
LOG_LEVEL=debug npm run dev

# Or set in .env
LOG_LEVEL=debug

# TypeScript compilation with verbose output
npm run build -- --verbose

# Run tests with verbose output
npm test -- --verbose
```

## AI Assistant Guidelines

### When Working on This Project

1. **TypeScript First**: Use strict TypeScript with explicit types everywhere
2. **Validate Everything**: Use Zod for all request/response validation
3. **Security Paranoia**: Always validate inputs, never skip authentication in production
4. **Async Always**: Use `async/await` for all I/O operations
5. **Type Everything**: Never use `any` unless absolutely necessary
6. **Test Coverage**: Write tests for new features, aim for 80%+ coverage
7. **Error Context**: Always log errors with context (what, where, why)
8. **Documentation**: Update docstrings and this CLAUDE_TYPESCRIPT.md when making changes

### Before Committing

- [ ] Code follows Prettier formatting (`npm run format`)
- [ ] Linting passes (`npm run lint`)
- [ ] Type checking passes (`npm run type-check`)
- [ ] All tests pass (`npm test`)
- [ ] Coverage meets target (`npm run test:coverage`)
- [ ] No secrets or sensitive data in code
- [ ] .env.example updated if new env vars added
- [ ] CLAUDE_TYPESCRIPT.md updated if architecture changed
- [ ] Commit message follows conventions

### Code Review Checklist

**For any pull request, verify:**
- [ ] Explicit types on all functions and variables
- [ ] Zod schemas for request/response validation
- [ ] Proper error handling with specific error types
- [ ] Security: authentication not bypassed
- [ ] Logging with appropriate levels
- [ ] Tests for happy path and error cases
- [ ] No blocking I/O operations
- [ ] Documentation updated

### Communication Patterns

When implementing features:
1. **Clarify requirements** - Ask about edge cases upfront
2. **Explain trade-offs** - Discuss security vs. convenience, performance vs. simplicity
3. **Suggest improvements** - Point out refactoring opportunities
4. **Highlight risks** - Call out security or performance concerns

## Resources

### Official Documentation

- **Express.js**: https://expressjs.com/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **Zod**: https://zod.dev/
- **Winston**: https://github.com/winstonjs/winston
- **Axios**: https://axios-http.com/docs/intro
- **Jest**: https://jestjs.io/docs/getting-started

### TypeScript Best Practices

- **TypeScript Deep Dive**: https://basarat.gitbook.io/typescript/
- **Type Challenges**: https://github.com/type-challenges/type-challenges
- **Effective TypeScript**: https://effectivetypescript.com/

### Testing & Quality

- **Jest Best Practices**: https://github.com/goldbergyoni/javascript-testing-best-practices
- **Supertest**: https://github.com/ladjs/supertest
- **ESLint**: https://eslint.org/docs/latest/
- **Prettier**: https://prettier.io/docs/en/

### Security

- **OWASP API Security Top 10**: https://owasp.org/www-project-api-security/
- **Node.js Security Best Practices**: https://nodejs.org/en/docs/guides/security/

## Version History

### Latest Update
- **Date**: 2025-11-15
- **Version**: 1.0.0
- **Status**: Production-ready specification (TypeScript/Node.js)
- **Changes**:
  - Initial TypeScript/Node.js version specification
  - Complete architecture based on Python version
  - Real-time debugging API with Server-Sent Events
  - Debug endpoints for model loading progress and inference monitoring
  - Performance metrics endpoint
  - Comprehensive code examples and patterns
  - Docker deployment configuration
  - Testing guidelines with Jest and Supertest

### Implementation Phases
See IMPLEMENTATION_PLAN_TYPESCRIPT.md for detailed phase-by-phase implementation guide.

---

**Note for AI Assistants**: This document reflects the **production-ready specification** for the LM Studio LAN Gateway (TypeScript/Node.js Edition). All code must follow these patterns. Update this document when architectural decisions change, new patterns emerge, or security considerations evolve. This is a **TypeScript/Node.js/Express.js project**.
