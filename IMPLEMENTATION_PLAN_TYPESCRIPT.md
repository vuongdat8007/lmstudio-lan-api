# LM Studio LAN Gateway - TypeScript/Node.js Implementation Plan

## Overview

This document outlines the phase-by-phase implementation plan for the **LM Studio LAN Gateway (TypeScript/Node.js Edition)**. Each phase builds upon the previous one, ensuring a systematic and testable development process.

**Target Stack:**
- **Runtime**: Node.js 20+ (LTS)
- **Language**: TypeScript 5.3+
- **Framework**: Express.js 4.x
- **Validation**: Zod
- **Logging**: Winston
- **HTTP Client**: axios
- **Testing**: Jest + Supertest
- **Deployment**: Docker + docker-compose

**Estimated Total Time**: 12-16 hours for experienced developer

---

## Phase 1: Project Foundation and Setup

**Goal**: Establish project structure, dependencies, and configuration files.

**Duration**: 1-1.5 hours

### Tasks

#### 1.1 Initialize Node.js Project
```bash
mkdir lmstudio-lan-api-typescript
cd lmstudio-lan-api-typescript
npm init -y
git init
```

#### 1.2 Install Core Dependencies
```bash
# Core runtime dependencies
npm install express cors helmet winston axios zod dotenv ipaddr.js

# TypeScript and type definitions
npm install -D typescript @types/node @types/express @types/cors

# Development tools
npm install -D tsx eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier eslint-config-prettier eslint-plugin-prettier

# Testing dependencies
npm install -D jest @types/jest ts-jest supertest @types/supertest
```

#### 1.3 Create TypeScript Configuration

**File: `tsconfig.json`**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

#### 1.4 Create ESLint Configuration

**File: `.eslintrc.json`**
```json
{
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module",
    "project": "./tsconfig.json"
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "prettier"
  ],
  "plugins": ["@typescript-eslint", "prettier"],
  "rules": {
    "prettier/prettier": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  },
  "env": {
    "node": true,
    "es2022": true
  }
}
```

#### 1.5 Create Prettier Configuration

**File: `.prettierrc`**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

#### 1.6 Create Jest Configuration

**File: `jest.config.js`**
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  coverageDirectory: 'coverage',
  verbose: true,
};
```

#### 1.7 Update package.json Scripts

**File: `package.json` (scripts section)**
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "clean": "rm -rf dist",
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "check": "npm run lint && npm run type-check && npm run test"
  }
}
```

#### 1.8 Create Environment Template

**File: `.env.example`**
```bash
# LM Studio API Configuration
LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# Gateway Server Configuration
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Security Configuration
# IMPORTANT: Change this in production!
GATEWAY_API_KEY=change-me-please

# IP Allow-listing
# Examples:
#   "*" - Allow all IPs (development only)
#   "192.168.0.0/24" - Allow subnet
#   "10.0.0.2,10.0.0.3" - Specific IPs
#   "192.168.0.0/24,10.0.0.0/24" - Multiple subnets
IP_ALLOWLIST=192.168.0.0/24,10.0.0.0/24

# Allow unauthenticated health checks
REQUIRE_AUTH_FOR_HEALTH=false

# Logging Configuration
LOG_LEVEL=info

# Node Environment
NODE_ENV=development
```

#### 1.9 Create .gitignore

**File: `.gitignore`**
```gitignore
# Environment
.env
.env.local
.env.*.local

# Node
node_modules/
npm-debug.log
yarn-error.log
package-lock.json

# Build
dist/
build/
*.tsbuildinfo

# Testing
coverage/
.jest/
.nyc_output/

# IDE
.vscode/
.idea/
*.swp
*.swo
*.sublime-*

# OS
.DS_Store
Thumbs.db
*.log

# Logs
logs/
*.log
```

#### 1.10 Create Basic Directory Structure
```bash
mkdir -p src/{config,middleware,routes,types,utils}
mkdir -p tests/{unit/{config,middleware,routes,utils},integration,fixtures}
```

### Deliverables

- [x] `package.json` with all dependencies and scripts
- [x] `tsconfig.json` with strict TypeScript configuration
- [x] `.eslintrc.json` with TypeScript ESLint rules
- [x] `.prettierrc` for code formatting
- [x] `jest.config.js` for testing
- [x] `.env.example` with all configuration options
- [x] `.gitignore` with comprehensive exclusions
- [x] Directory structure created

### Testing Phase 1

```bash
# Verify TypeScript compilation works
npm run type-check

# Verify ESLint works
npm run lint

# Verify Prettier works
npm run format

# Verify all tools are properly configured
npm run check
```

---

## Phase 2: Core Infrastructure

**Goal**: Implement configuration management, logging, and middleware foundations.

**Duration**: 2-3 hours

### Tasks

#### 2.1 Create Settings Module with Zod Validation

**File: `src/config/settings.ts`**
```typescript
import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Environment schema with validation
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

// Parse and validate environment variables
const env = envSchema.parse(process.env);

// Export settings object
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
} as const;
```

#### 2.2 Create Logger Configuration

**File: `src/config/logger.ts`**
```typescript
import winston from 'winston';
import { settings } from './settings';

// Custom format for console output
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.colorize(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length > 0 ? ` ${JSON.stringify(meta)}` : '';
    return `${timestamp} [${level}]: ${message}${metaStr}`;
  })
);

// Create logger instance
const logger = winston.createLogger({
  level: settings.logLevel,
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: consoleFormat,
    }),
  ],
});

export default logger;
```

#### 2.3 Create IP Allowlist Middleware

**File: `src/middleware/ipAllowlist.ts`**
```typescript
import { Request, Response, NextFunction } from 'express';
import { Address4, Address6 } from 'ipaddr.js';
import logger from '../config/logger';
import { settings } from '../config/settings';

/**
 * Check if an IP address is within a CIDR range
 */
function ipInCidr(ip: string, cidr: string): boolean {
  try {
    // Handle CIDR notation
    if (cidr.includes('/')) {
      const [network, prefixStr] = cidr.split('/');
      const prefix = parseInt(prefixStr, 10);

      // Determine IP version
      const ipAddr = ip.includes(':') ? Address6.parse(ip) : Address4.parse(ip);
      const networkAddr = network.includes(':')
        ? Address6.parse(network)
        : Address4.parse(network);

      // Both must be same version
      if (ipAddr.kind() !== networkAddr.kind()) {
        return false;
      }

      // Check if IP matches network/prefix
      return ipAddr.match(networkAddr, prefix);
    } else {
      // Exact IP match
      return ip === cidr;
    }
  } catch (error) {
    logger.error('Error parsing IP/CIDR:', { ip, cidr, error });
    return false;
  }
}

/**
 * Middleware to enforce IP allowlist
 */
export function ipAllowlistMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const allowlist = settings.ipAllowlistItems;

  // Allow all if wildcard
  if (allowlist.includes('*')) {
    return next();
  }

  // Get client IP (handle IPv6-mapped IPv4)
  let clientIp = req.ip || req.socket.remoteAddress || '';
  if (clientIp.startsWith('::ffff:')) {
    clientIp = clientIp.substring(7);
  }

  // Check if IP is in allowlist
  const allowed = allowlist.some((item) => {
    if (item === clientIp) return true;
    if (item.includes('/')) return ipInCidr(clientIp, item);
    return false;
  });

  if (!allowed) {
    logger.warn('Forbidden IP attempted access', {
      ip: clientIp,
      path: req.path,
      allowlist,
    });
    res.status(403).json({ error: 'Forbidden' });
    return;
  }

  next();
}
```

#### 2.4 Create API Key Middleware

**File: `src/middleware/apiKey.ts`**
```typescript
import { Request, Response, NextFunction } from 'express';
import logger from '../config/logger';
import { settings } from '../config/settings';

/**
 * Middleware to enforce API key authentication
 */
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

  // Get API key from header
  const apiKey = req.headers['x-api-key'];

  // Validate API key
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

### Deliverables

- [x] `src/config/settings.ts` - Zod-based configuration with validation
- [x] `src/config/logger.ts` - Winston logger with structured logging
- [x] `src/middleware/ipAllowlist.ts` - IP/CIDR allowlist middleware
- [x] `src/middleware/apiKey.ts` - API key authentication middleware

### Testing Phase 2

**File: `tests/unit/config/settings.test.ts`**
```typescript
import { settings } from '../../../src/config/settings';

describe('Settings', () => {
  it('should load settings from environment', () => {
    expect(settings.gatewayPort).toBeDefined();
    expect(typeof settings.apiKeyEnabled).toBe('boolean');
  });

  it('should parse IP allowlist items', () => {
    expect(Array.isArray(settings.ipAllowlistItems)).toBe(true);
  });
});
```

**File: `tests/unit/middleware/ipAllowlist.test.ts`**
```typescript
import { Request, Response, NextFunction } from 'express';
import { ipAllowlistMiddleware } from '../../../src/middleware/ipAllowlist';

describe('IP Allowlist Middleware', () => {
  let mockReq: Partial<Request>;
  let mockRes: Partial<Response>;
  let mockNext: NextFunction;

  beforeEach(() => {
    mockReq = {
      ip: '192.168.0.100',
      path: '/test',
      socket: { remoteAddress: '192.168.0.100' } as any,
    };
    mockRes = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };
    mockNext = jest.fn();
  });

  it('should allow wildcard access', () => {
    ipAllowlistMiddleware(mockReq as Request, mockRes as Response, mockNext);
    expect(mockNext).toHaveBeenCalled();
  });

  // Add more tests for CIDR ranges, specific IPs, etc.
});
```

**File: `tests/unit/middleware/apiKey.test.ts`**
```typescript
import { Request, Response, NextFunction } from 'express';
import { apiKeyMiddleware } from '../../../src/middleware/apiKey';

describe('API Key Middleware', () => {
  let mockReq: Partial<Request>;
  let mockRes: Partial<Response>;
  let mockNext: NextFunction;

  beforeEach(() => {
    mockReq = {
      path: '/test',
      headers: {},
    };
    mockRes = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };
    mockNext = jest.fn();
  });

  it('should allow requests with valid API key', () => {
    mockReq.headers = { 'x-api-key': process.env.GATEWAY_API_KEY };
    apiKeyMiddleware(mockReq as Request, mockRes as Response, mockNext);
    expect(mockNext).toHaveBeenCalled();
  });

  it('should reject requests without API key', () => {
    apiKeyMiddleware(mockReq as Request, mockRes as Response, mockNext);
    expect(mockRes.status).toHaveBeenCalledWith(401);
  });
});
```

**Run tests:**
```bash
npm test
```

---

## Phase 3: Type Definitions and Schemas

**Goal**: Define all Zod schemas and TypeScript types for request/response models.

**Duration**: 1-2 hours

### Tasks

#### 3.1 Create Type Definitions and Zod Schemas

**File: `src/types/models.ts`**
```typescript
import { z } from 'zod';

// ===== Load Configuration Schemas =====

export const LoadConfigSchema = z.object({
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

export type LoadConfig = z.infer<typeof LoadConfigSchema>;

// ===== Inference Parameter Schemas =====

export const DefaultInferenceSchema = z.object({
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().int().positive().optional(),
  topP: z.number().min(0).max(1).optional(),
  topK: z.number().int().nonnegative().optional(),
  repeatPenalty: z.number().min(0).optional(),
  stopStrings: z.array(z.string()).optional(),
  stream: z.boolean().optional(),
});

export type DefaultInference = z.infer<typeof DefaultInferenceSchema>;

// ===== Admin API Request/Response Schemas =====

export const LoadModelRequestSchema = z.object({
  modelKey: z.string().min(1, 'modelKey is required'),
  instanceId: z.string().optional(),
  loadConfig: LoadConfigSchema.optional(),
  ttlSeconds: z.number().int().nonnegative().optional(),
  defaultInference: DefaultInferenceSchema.optional(),
  activate: z.boolean().default(true),
});

export type LoadModelRequest = z.infer<typeof LoadModelRequestSchema>;

export const LoadModelResponseSchema = z.object({
  status: z.literal('loaded'),
  modelKey: z.string(),
  instanceId: z.string().nullable(),
  activated: z.boolean(),
  message: z.string().optional(),
});

export type LoadModelResponse = z.infer<typeof LoadModelResponseSchema>;

export const UnloadModelRequestSchema = z.object({
  modelKey: z.string().min(1, 'modelKey is required'),
  instanceId: z.string().nullable().optional(),
});

export type UnloadModelRequest = z.infer<typeof UnloadModelRequestSchema>;

export const UnloadModelResponseSchema = z.object({
  status: z.literal('unloaded'),
  modelKey: z.string(),
  instanceId: z.string().nullable(),
  message: z.string().optional(),
});

export type UnloadModelResponse = z.infer<typeof UnloadModelResponseSchema>;

export const ActivateModelRequestSchema = z.object({
  modelKey: z.string().min(1, 'modelKey is required'),
  instanceId: z.string().nullable().optional(),
  defaultInference: DefaultInferenceSchema.optional(),
});

export type ActivateModelRequest = z.infer<typeof ActivateModelRequestSchema>;

export const ActivateModelResponseSchema = z.object({
  status: z.literal('activated'),
  modelKey: z.string(),
  instanceId: z.string().nullable(),
  defaultInference: z.record(z.any()),
  message: z.string().optional(),
});

export type ActivateModelResponse = z.infer<typeof ActivateModelResponseSchema>;

// ===== Application State Interfaces =====

export interface ActiveModel {
  modelKey: string | null;
  instanceId: string | null;
  defaultInference: Record<string, any>;
}

export interface OperationInfo {
  type: 'model_load' | 'inference' | null;
  modelKey?: string;
  progress?: number;
  startedAt?: string;
  elapsedMs?: number;
}

export interface RequestInfo {
  requestId: string;
  status: 'pending' | 'completed' | 'failed';
  tokensGenerated?: number;
  timeMs?: number;
  timestamp: string;
}

export interface DebugState {
  status: 'idle' | 'loading_model' | 'processing_inference' | 'error';
  currentOperation: OperationInfo | null;
  recentRequests: RequestInfo[];
  totalRequests: number;
  totalErrors: number;
}

export interface AppState {
  activeModel: ActiveModel;
  debugState: DebugState;
}

// ===== Debug Event Types =====

export interface DebugEvent {
  type: string;
  data: Record<string, any>;
}
```

### Deliverables

- [x] `src/types/models.ts` - Complete type definitions and Zod schemas

### Testing Phase 3

**File: `tests/unit/types/models.test.ts`**
```typescript
import {
  LoadModelRequestSchema,
  DefaultInferenceSchema,
  LoadConfigSchema,
} from '../../../src/types/models';

describe('Model Schemas', () => {
  describe('LoadModelRequestSchema', () => {
    it('should validate valid load model request', () => {
      const validRequest = {
        modelKey: 'test-model',
        activate: true,
      };
      const result = LoadModelRequestSchema.safeParse(validRequest);
      expect(result.success).toBe(true);
    });

    it('should reject invalid load model request', () => {
      const invalidRequest = {
        // Missing modelKey
        activate: true,
      };
      const result = LoadModelRequestSchema.safeParse(invalidRequest);
      expect(result.success).toBe(false);
    });
  });

  describe('DefaultInferenceSchema', () => {
    it('should validate temperature range', () => {
      const validInference = { temperature: 0.7 };
      const result = DefaultInferenceSchema.safeParse(validInference);
      expect(result.success).toBe(true);

      const invalidInference = { temperature: 3.0 }; // Out of range
      const result2 = DefaultInferenceSchema.safeParse(invalidInference);
      expect(result2.success).toBe(false);
    });
  });
});
```

---

## Phase 4: Admin API Implementation

**Goal**: Implement model management endpoints.

**Duration**: 2-3 hours

### Tasks

#### 4.1 Create Admin Router

**File: `src/routes/admin.ts`**
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import axios from 'axios';
import logger from '../config/logger';
import { settings } from '../config/settings';
import {
  LoadModelRequestSchema,
  UnloadModelRequestSchema,
  ActivateModelRequestSchema,
  AppState,
} from '../types/models';

export function createAdminRouter(appState: AppState): Router {
  const router = Router();

  /**
   * GET /admin/models - List available models
   */
  router.get('/models', async (req: Request, res: Response, next: NextFunction) => {
    try {
      logger.info('Fetching model list from LM Studio');

      const response = await axios.get(`${settings.lmStudioBaseUrl}/v1/models`, {
        timeout: 10000,
      });

      res.json(response.data);
    } catch (error) {
      logger.error('Error fetching models:', error);
      if (axios.isAxiosError(error)) {
        next(new Error('LM Studio API unreachable'));
      } else {
        next(error);
      }
    }
  });

  /**
   * POST /admin/models/load - Load a model
   */
  router.post('/models/load', async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Validate request
      const payload = LoadModelRequestSchema.parse(req.body);

      logger.info('Loading model', {
        modelKey: payload.modelKey,
        instanceId: payload.instanceId,
      });

      // Update debug state
      appState.debugState.status = 'loading_model';
      appState.debugState.currentOperation = {
        type: 'model_load',
        modelKey: payload.modelKey,
        progress: 0,
        startedAt: new Date().toISOString(),
      };

      // Call LM Studio API to load model
      // Note: Actual implementation depends on LM Studio's API
      // This is a placeholder that simulates the operation
      const response = await axios.post(
        `${settings.lmStudioBaseUrl}/v1/models/load`,
        {
          model: payload.modelKey,
          ...(payload.loadConfig && { config: payload.loadConfig }),
        },
        { timeout: 60000 }
      );

      // Activate model if requested
      if (payload.activate) {
        appState.activeModel = {
          modelKey: payload.modelKey,
          instanceId: payload.instanceId || null,
          defaultInference: payload.defaultInference || {},
        };
        logger.info('Model activated as default', { modelKey: payload.modelKey });
      }

      // Update debug state
      appState.debugState.status = 'idle';
      appState.debugState.currentOperation = null;

      res.json({
        status: 'loaded',
        modelKey: payload.modelKey,
        instanceId: payload.instanceId || null,
        activated: payload.activate,
        message: 'Model loaded successfully',
      });
    } catch (error) {
      appState.debugState.status = 'error';
      appState.debugState.totalErrors++;
      next(error);
    }
  });

  /**
   * POST /admin/models/unload - Unload a model
   */
  router.post('/models/unload', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const payload = UnloadModelRequestSchema.parse(req.body);

      logger.info('Unloading model', {
        modelKey: payload.modelKey,
        instanceId: payload.instanceId,
      });

      // Call LM Studio API to unload model
      await axios.post(
        `${settings.lmStudioBaseUrl}/v1/models/unload`,
        {
          model: payload.modelKey,
        },
        { timeout: 30000 }
      );

      // Clear active model if it's the one being unloaded
      if (appState.activeModel.modelKey === payload.modelKey) {
        appState.activeModel = {
          modelKey: null,
          instanceId: null,
          defaultInference: {},
        };
        logger.info('Active model cleared');
      }

      res.json({
        status: 'unloaded',
        modelKey: payload.modelKey,
        instanceId: payload.instanceId || null,
        message: 'Model unloaded successfully',
      });
    } catch (error) {
      next(error);
    }
  });

  /**
   * POST /admin/models/activate - Activate a model as default
   */
  router.post(
    '/models/activate',
    async (req: Request, res: Response, next: NextFunction) => {
      try {
        const payload = ActivateModelRequestSchema.parse(req.body);

        logger.info('Activating model', {
          modelKey: payload.modelKey,
          instanceId: payload.instanceId,
        });

        // Update active model
        appState.activeModel = {
          modelKey: payload.modelKey,
          instanceId: payload.instanceId || null,
          defaultInference: payload.defaultInference || {},
        };

        res.json({
          status: 'activated',
          modelKey: payload.modelKey,
          instanceId: payload.instanceId || null,
          defaultInference: appState.activeModel.defaultInference,
          message: 'Model activated successfully',
        });
      } catch (error) {
        next(error);
      }
    }
  );

  return router;
}
```

### Deliverables

- [x] `src/routes/admin.ts` - Complete admin API router

### Testing Phase 4

**File: `tests/integration/admin.test.ts`**
```typescript
import request from 'supertest';
import { Express } from 'express';
import { createApp } from '../../src/index';

describe('Admin API Integration Tests', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  describe('GET /admin/models', () => {
    it('should return model list with valid API key', async () => {
      const response = await request(app)
        .get('/admin/models')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '');

      expect(response.status).toBe(200);
      // Add more specific assertions based on expected response
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
      expect(response.body.status).toBe('loaded');
    });
  });
});
```

---

## Phase 5: Debug API Implementation

**Goal**: Implement real-time debugging endpoints with Server-Sent Events.

**Duration**: 2-3 hours

### Tasks

#### 5.1 Create Event Broadcaster Utility

**File: `src/utils/eventBroadcaster.ts`**
```typescript
import { EventEmitter } from 'events';
import logger from '../config/logger';

// Global event emitter for broadcasting debug events
const debugEventEmitter = new EventEmitter();
debugEventEmitter.setMaxListeners(100); // Support many concurrent clients

export interface DebugEventData {
  type: string;
  data: Record<string, any>;
}

/**
 * Broadcast a debug event to all connected SSE clients
 */
export function broadcastDebugEvent(eventType: string, data: Record<string, any>): void {
  const event: DebugEventData = {
    type: eventType,
    data: {
      ...data,
      timestamp: new Date().toISOString(),
    },
  };

  debugEventEmitter.emit('debug-event', event);
  logger.debug('Debug event broadcasted', { type: eventType });
}

/**
 * Get the debug event emitter
 */
export function getDebugEventEmitter(): EventEmitter {
  return debugEventEmitter;
}
```

#### 5.2 Create Debug Router

**File: `src/routes/debug.ts`**
```typescript
import { Router, Request, Response } from 'express';
import logger from '../config/logger';
import { AppState } from '../types/models';
import { getDebugEventEmitter, DebugEventData } from '../utils/eventBroadcaster';

export function createDebugRouter(appState: AppState): Router {
  const router = Router();
  const debugEventEmitter = getDebugEventEmitter();

  /**
   * GET /debug/stream - Server-Sent Events stream for real-time debugging
   */
  router.get('/stream', (req: Request, res: Response): void => {
    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

    logger.info('Client connected to debug stream', { ip: req.ip });

    // Send initial connection event
    res.write(
      `event: connected\ndata: ${JSON.stringify({
        timestamp: new Date().toISOString(),
        message: 'Debug stream connected',
      })}\n\n`
    );

    // Event listener for broadcasting
    const eventListener = (event: DebugEventData) => {
      res.write(`event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`);
    };

    debugEventEmitter.on('debug-event', eventListener);

    // Keep-alive ping every 30 seconds
    const keepAliveInterval = setInterval(() => {
      res.write(': keep-alive\n\n');
    }, 30000);

    // Cleanup on client disconnect
    req.on('close', () => {
      debugEventEmitter.off('debug-event', eventListener);
      clearInterval(keepAliveInterval);
      logger.info('Client disconnected from debug stream', { ip: req.ip });
    });
  });

  /**
   * GET /debug/status - Current debug status snapshot
   */
  router.get('/status', (req: Request, res: Response): void => {
    res.json({
      status: appState.debugState.status,
      currentOperation: appState.debugState.currentOperation,
      activeModel: appState.activeModel,
      recentRequests: appState.debugState.recentRequests.slice(-10), // Last 10
      totalRequests: appState.debugState.totalRequests,
      totalErrors: appState.debugState.totalErrors,
    });
  });

  /**
   * GET /debug/metrics - Performance metrics
   */
  router.get('/metrics', (req: Request, res: Response): void => {
    res.json({
      modelInfo: {
        modelKey: appState.activeModel.modelKey,
        instanceId: appState.activeModel.instanceId,
      },
      performance: {
        totalRequests: appState.debugState.totalRequests,
        totalErrors: appState.debugState.totalErrors,
        recentRequestCount: appState.debugState.recentRequests.length,
      },
      system: {
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
      },
    });
  });

  return router;
}
```

### Deliverables

- [x] `src/utils/eventBroadcaster.ts` - SSE event broadcasting utility
- [x] `src/routes/debug.ts` - Complete debug API router with SSE

### Testing Phase 5

**File: `tests/integration/debug.test.ts`**
```typescript
import request from 'supertest';
import { Express } from 'express';
import { createApp } from '../../src/index';

describe('Debug API Integration Tests', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  describe('GET /debug/status', () => {
    it('should return current status', async () => {
      const response = await request(app)
        .get('/debug/status')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status');
      expect(response.body).toHaveProperty('activeModel');
    });
  });

  describe('GET /debug/metrics', () => {
    it('should return performance metrics', async () => {
      const response = await request(app)
        .get('/debug/metrics')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('performance');
      expect(response.body).toHaveProperty('system');
    });
  });

  // Note: SSE testing requires special handling
  // Consider using EventSource polyfill or specific SSE testing libraries
});
```

---

## Phase 6: Proxy Router Implementation

**Goal**: Implement transparent proxy for /v1/* endpoints with model injection.

**Duration**: 2-3 hours

### Tasks

#### 6.1 Create Proxy Router

**File: `src/routes/proxy.ts`**
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import axios, { AxiosResponse } from 'axios';
import logger from '../config/logger';
import { settings } from '../config/settings';
import { AppState } from '../types/models';
import { broadcastDebugEvent } from '../utils/eventBroadcaster';

export function createProxyRouter(appState: AppState): Router {
  const router = Router();

  /**
   * Proxy all /v1/* requests to LM Studio
   */
  router.all('/v1/*', async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    try {
      // Get the full path after /v1
      const targetPath = req.path;
      const targetUrl = `${settings.lmStudioBaseUrl}${targetPath}`;

      logger.info('Proxying request to LM Studio', {
        method: req.method,
        path: targetPath,
        requestId,
      });

      // Broadcast inference start event
      broadcastDebugEvent('inference_start', {
        requestId,
        method: req.method,
        path: targetPath,
      });

      // Clone and modify request body if needed
      let requestBody = req.body;

      // Auto-inject active model and default inference params for completion requests
      if (
        (targetPath.includes('/chat/completions') || targetPath.includes('/completions')) &&
        req.method === 'POST'
      ) {
        requestBody = { ...req.body };

        // Inject model if not specified
        if (!requestBody.model && appState.activeModel.modelKey) {
          requestBody.model = appState.activeModel.modelKey;
          logger.debug('Injected active model', { model: requestBody.model });
        }

        // Inject default inference parameters
        const defaults = appState.activeModel.defaultInference;
        if (defaults.temperature !== undefined && requestBody.temperature === undefined) {
          requestBody.temperature = defaults.temperature;
        }
        if (defaults.maxTokens !== undefined && requestBody.max_tokens === undefined) {
          requestBody.max_tokens = defaults.maxTokens;
        }
        if (defaults.topP !== undefined && requestBody.top_p === undefined) {
          requestBody.top_p = defaults.topP;
        }
        // Add more default parameters as needed
      }

      // Forward request to LM Studio
      const response: AxiosResponse = await axios({
        method: req.method,
        url: targetUrl,
        headers: {
          ...req.headers,
          host: new URL(settings.lmStudioBaseUrl).host,
          // Remove gateway-specific headers
          'x-api-key': undefined,
        },
        data: requestBody,
        params: req.query,
        responseType: requestBody.stream ? 'stream' : 'json',
        timeout: 120000, // 2 minutes for long-running requests
      });

      // Update debug state
      appState.debugState.totalRequests++;
      appState.debugState.recentRequests.push({
        requestId,
        status: 'completed',
        timeMs: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      });

      // Keep only last 100 requests
      if (appState.debugState.recentRequests.length > 100) {
        appState.debugState.recentRequests = appState.debugState.recentRequests.slice(-100);
      }

      // Broadcast inference complete event
      broadcastDebugEvent('inference_complete', {
        requestId,
        totalTimeMs: Date.now() - startTime,
      });

      // Handle streaming response
      if (requestBody.stream && response.data.pipe) {
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        response.data.pipe(res);
      } else {
        // Regular JSON response
        res.status(response.status).json(response.data);
      }
    } catch (error) {
      appState.debugState.totalErrors++;

      broadcastDebugEvent('error', {
        requestId,
        error: axios.isAxiosError(error) ? error.message : 'Unknown error',
        totalTimeMs: Date.now() - startTime,
      });

      logger.error('Proxy request failed', {
        requestId,
        error: axios.isAxiosError(error) ? error.message : error,
      });

      if (axios.isAxiosError(error)) {
        const status = error.response?.status || 503;
        const data = error.response?.data || { error: 'LM Studio API error' };
        res.status(status).json(data);
      } else {
        next(error);
      }
    }
  });

  return router;
}
```

### Deliverables

- [x] `src/routes/proxy.ts` - Complete proxy router with model injection

### Testing Phase 6

**File: `tests/integration/proxy.test.ts`**
```typescript
import request from 'supertest';
import { Express } from 'express';
import { createApp } from '../../src/index';

describe('Proxy API Integration Tests', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  describe('POST /v1/chat/completions', () => {
    it('should proxy chat completion request', async () => {
      const payload = {
        messages: [{ role: 'user', content: 'Hello!' }],
        // model will be auto-injected
      };

      const response = await request(app)
        .post('/v1/chat/completions')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '')
        .send(payload);

      // Response depends on LM Studio being available
      // You may want to mock axios for unit tests
      expect([200, 503]).toContain(response.status);
    });
  });
});
```

---

## Phase 7: Main Application Assembly

**Goal**: Create main Express application with all components integrated.

**Duration**: 1-2 hours

### Tasks

#### 7.1 Create Main Application File

**File: `src/index.ts`**
```typescript
import express, { Request, Response, NextFunction, Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { z } from 'zod';
import logger from './config/logger';
import { settings } from './config/settings';
import { ipAllowlistMiddleware } from './middleware/ipAllowlist';
import { apiKeyMiddleware } from './middleware/apiKey';
import { createAdminRouter } from './routes/admin';
import { createDebugRouter } from './routes/debug';
import { createProxyRouter } from './routes/proxy';
import { AppState } from './types/models';

/**
 * Create and configure Express application
 */
export function createApp(): Express {
  const app = express();

  // Initialize application state
  const appState: AppState = {
    activeModel: {
      modelKey: null,
      instanceId: null,
      defaultInference: {},
    },
    debugState: {
      status: 'idle',
      currentOperation: null,
      recentRequests: [],
      totalRequests: 0,
      totalErrors: 0,
    },
  };

  // Attach state to app locals
  app.locals.appState = appState;

  // Security middleware
  app.use(helmet());
  app.use(cors());

  // Body parsing
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Custom middleware
  app.use(ipAllowlistMiddleware);
  app.use(apiKeyMiddleware);

  // Health check endpoint (before routers)
  app.get('/health', (req: Request, res: Response) => {
    res.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    });
  });

  // Register routers
  app.use('/admin', createAdminRouter(appState));
  app.use('/debug', createDebugRouter(appState));
  app.use(createProxyRouter(appState));

  // 404 handler
  app.use((req: Request, res: Response) => {
    logger.warn('Route not found', { path: req.path, method: req.method });
    res.status(404).json({ error: 'Not found' });
  });

  // Global error handler
  app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    // Handle Zod validation errors
    if (err instanceof z.ZodError) {
      logger.warn('Validation error', {
        path: req.path,
        errors: err.errors,
      });
      res.status(400).json({
        error: 'Validation failed',
        details: err.errors,
      });
      return;
    }

    // Handle other errors
    logger.error('Unhandled error', {
      path: req.path,
      error: err.message,
      stack: err.stack,
    });

    res.status(500).json({
      error: 'Internal server error',
      ...(settings.nodeEnv === 'development' && { details: err.message }),
    });
  });

  return app;
}

/**
 * Start the server
 */
export function startServer(): void {
  const app = createApp();

  const server = app.listen(settings.gatewayPort, settings.gatewayHost, () => {
    logger.info('='.repeat(60));
    logger.info('LM Studio LAN Gateway (TypeScript) v1.0.0');
    logger.info('='.repeat(60));
    logger.info(`LM Studio URL: ${settings.lmStudioBaseUrl}`);
    logger.info(`Gateway: http://${settings.gatewayHost}:${settings.gatewayPort}`);
    logger.info(`API Key Auth: ${settings.apiKeyEnabled ? 'enabled' : 'disabled'}`);
    logger.info(`IP Allowlist: ${settings.ipAllowlistItems.join(', ') || '*'}`);
    logger.info(`Environment: ${settings.nodeEnv}`);
    logger.info(`Log Level: ${settings.logLevel}`);
    logger.info('='.repeat(60));
    logger.info('Gateway started successfully');
  });

  // Graceful shutdown
  const shutdown = (signal: string) => {
    logger.info(`${signal} signal received: closing HTTP server`);
    server.close(() => {
      logger.info('HTTP server closed');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

// Start server if this is the main module
if (require.main === module) {
  startServer();
}
```

### Deliverables

- [x] `src/index.ts` - Complete main application file

### Testing Phase 7

**File: `tests/integration/app.test.ts`**
```typescript
import request from 'supertest';
import { createApp } from '../../src/index';

describe('Application Integration Tests', () => {
  const app = createApp();

  describe('Health Check', () => {
    it('should return health status', async () => {
      const response = await request(app).get('/health');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'ok');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('404 Handler', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await request(app).get('/unknown-route');

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('error', 'Not found');
    });
  });

  describe('Error Handler', () => {
    it('should handle validation errors', async () => {
      const response = await request(app)
        .post('/admin/models/load')
        .set('X-API-Key', process.env.GATEWAY_API_KEY || '')
        .send({ invalid: 'payload' });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('error', 'Validation failed');
    });
  });
});
```

**Run all tests:**
```bash
npm run test:coverage
```

---

## Phase 8: Docker Deployment Configuration

**Goal**: Create Docker and docker-compose configurations for containerized deployment.

**Duration**: 1 hour

### Tasks

#### 8.1 Create Dockerfile

**File: `Dockerfile`**
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

#### 8.2 Create .dockerignore

**File: `.dockerignore`**
```
# Git
.git
.gitignore

# Node
node_modules
npm-debug.log
yarn-error.log

# Build
dist
build
*.tsbuildinfo

# Tests
tests
coverage
.jest

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs
*.log

# Documentation
docs
*.md
!README.md

# Other
scripts
```

#### 8.3 Create docker-compose.yml

**File: `docker-compose.yml`**
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
    # Note: LM Studio must be running on the host
    # On Docker Desktop (Mac/Windows), use host.docker.internal:1234
    # On Linux, use host network mode or bridge with host IP
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"  # Docker Desktop
    # network_mode: "host"  # Linux alternative
```

### Deliverables

- [x] `Dockerfile` - Multi-stage Docker build
- [x] `.dockerignore` - Docker build optimization
- [x] `docker-compose.yml` - Docker Compose configuration

### Testing Phase 8

```bash
# Build Docker image
docker build -t lmstudio-gateway-ts .

# Run with docker-compose
docker-compose up -d

# Check health
curl http://localhost:8001/health

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Phase 9: Documentation and Polish

**Goal**: Create comprehensive README and finalize project.

**Duration**: 1-2 hours

### Tasks

#### 9.1 Create README.md

**File: `README.md`**
```markdown
# LM Studio LAN Gateway (TypeScript Edition)

A production-ready LAN-based API gateway for LM Studio, enabling secure local network access to LM Studio's language model capabilities.

## Features

- **Admin API**: Load, unload, and manage models remotely
- **Transparent Proxy**: Forward all OpenAI-compatible `/v1/*` requests to LM Studio
- **Security**: API key authentication and IP/CIDR-based access control
- **Real-time Debugging**: Server-Sent Events for live model loading and inference monitoring
- **Production-Ready**: TypeScript, comprehensive error handling, structured logging

## Tech Stack

- **Runtime**: Node.js 20+ (LTS)
- **Language**: TypeScript 5.3+
- **Framework**: Express.js
- **Validation**: Zod
- **Logging**: Winston
- **HTTP Client**: axios
- **Testing**: Jest + Supertest

## Quick Start

### Prerequisites

- Node.js 20+ installed
- LM Studio running on `http://127.0.0.1:1234` (configurable)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/lmstudio-lan-api-typescript.git
cd lmstudio-lan-api-typescript
```

2. Install dependencies
```bash
npm install
```

3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Start development server
```bash
npm run dev
```

5. Build for production
```bash
npm run build
npm start
```

## Configuration

See `.env.example` for all available configuration options.

Key settings:
- `GATEWAY_API_KEY`: API key for authentication (REQUIRED for production)
- `IP_ALLOWLIST`: Comma-separated list of allowed IPs/CIDR ranges
- `LMSTUDIO_BASE_URL`: LM Studio API URL (default: http://127.0.0.1:1234)

## API Endpoints

### Admin API
- `GET /admin/models` - List available models
- `POST /admin/models/load` - Load a model
- `POST /admin/models/unload` - Unload a model
- `POST /admin/models/activate` - Activate a model as default

### Debug API
- `GET /debug/stream` - SSE stream for real-time debugging
- `GET /debug/status` - Current status snapshot
- `GET /debug/metrics` - Performance metrics

### Proxy API
- `/v1/*` - All OpenAI-compatible endpoints (proxied to LM Studio)

### Health Check
- `GET /health` - Health status

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Development

```bash
# Run in development mode with auto-reload
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run type-check

# Run all checks
npm run check
```

## Security

- Always set `GATEWAY_API_KEY` in production
- Use IP allow-listing to restrict access to known networks
- Never expose to public internet (LAN only)
- Use HTTPS via reverse proxy (nginx, Traefik)

## License

MIT

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.
```

#### 9.2 Run Final Checks

```bash
# Type checking
npm run type-check

# Linting
npm run lint:fix

# Formatting
npm run format

# All tests
npm run test:coverage

# Build
npm run build

# Run final check
npm run check
```

### Deliverables

- [x] `README.md` - Comprehensive project documentation
- [x] All code formatted and linted
- [x] All tests passing
- [x] Production build successful

---

## Post-Implementation Checklist

### Code Quality
- [ ] All TypeScript compilation passes with no errors
- [ ] ESLint passes with no errors/warnings
- [ ] Prettier formatting applied to all files
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥80%

### Security
- [ ] No secrets or API keys in code
- [ ] .env.example updated with all variables
- [ ] IP allowlist properly configured
- [ ] API key authentication tested

### Documentation
- [ ] README.md complete and accurate
- [ ] CLAUDE_TYPESCRIPT.md updated with final patterns
- [ ] API endpoints documented
- [ ] Environment variables documented

### Deployment
- [ ] Docker build successful
- [ ] docker-compose deployment tested
- [ ] Health check endpoint working
- [ ] Graceful shutdown tested

### Functionality
- [ ] All admin endpoints working
- [ ] All debug endpoints working
- [ ] Proxy endpoints working
- [ ] SSE streaming working
- [ ] Model injection working
- [ ] Error handling tested

---

## Summary

This implementation plan provides a systematic approach to building the LM Studio LAN Gateway in TypeScript/Node.js. Each phase builds upon the previous one, ensuring:

1. **Solid Foundation**: Proper tooling and configuration from the start
2. **Type Safety**: Strict TypeScript with Zod validation
3. **Comprehensive Testing**: Unit and integration tests throughout
4. **Production-Ready**: Docker deployment, security, logging
5. **Developer Experience**: Hot reload, linting, formatting, type checking

**Total Estimated Time**: 12-16 hours

**Key Success Metrics**:
- All tests passing with ≥80% coverage
- Docker deployment working
- All API endpoints functional
- Real-time debugging via SSE operational
- Security features (API key, IP allowlist) working

For detailed patterns and conventions, refer to **CLAUDE_TYPESCRIPT.md**.
