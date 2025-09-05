import { EventEmitter } from 'events';
import { logger } from '../utils/logger';

/**
 * Performance Monitor Service
 * Tracks and analyzes MCPControl performance metrics
 */
interface PerformanceMetrics {
  startTime: number;
  toolExecutions: number;
  workflowExecutions: number;
  totalExecutionTime: number;
  averageExecutionTime: number;
  errorCount: number;
  successRate: number;
}

export class PerformanceMonitor extends EventEmitter {
  private isInitialized = false;
  private isRunning = false;
  private metrics: PerformanceMetrics | null = null;

  constructor() {
    super();
  }

  /**
   * Initialize the performance monitor
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      logger.warn('PerformanceMonitor already initialized');
      return;
    }

    try {
      logger.info('🔧 Initializing PerformanceMonitor...');
      
      this.metrics = {
        startTime: Date.now(),
        toolExecutions: 0,
        workflowExecutions: 0,
        totalExecutionTime: 0,
        averageExecutionTime: 0,
        errorCount: 0,
        successRate: 1.0,
      };
      
      this.isInitialized = true;
      logger.info('✅ PerformanceMonitor initialized successfully');

    } catch (error) {
      logger.error('💥 Failed to initialize PerformanceMonitor:', error);
      throw error;
    }
  }

  /**
   * Start performance monitoring
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('PerformanceMonitor already running');
      return;
    }

    logger.info('📊 Starting performance monitoring...');
    this.isRunning = true;
    logger.info('✅ Performance monitoring started');
  }

  /**
   * Stop performance monitoring
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      logger.warn('PerformanceMonitor not running');
      return;
    }

    logger.info('🛑 Stopping performance monitoring...');
    this.isRunning = false;
    logger.info('✅ Performance monitoring stopped');
  }

  /**
   * Get current metrics
   */
  async getMetrics(): Promise<Record<string, unknown>> {
    if (!this.metrics) return {};
    return {
      ...this.metrics,
      uptime: Date.now() - this.metrics.startTime,
      isRunning: this.isRunning,
    };
  }

  /**
   * Get health status
   */
  async getHealthStatus(): Promise<{ status: 'healthy' | 'initializing'; isRunning: boolean; metricsCollected: number }> {
    return {
      status: this.isInitialized ? 'healthy' : 'initializing',
      isRunning: this.isRunning,
      metricsCollected: this.metrics ? Object.keys(this.metrics).length : 0,
    };
  }
}
