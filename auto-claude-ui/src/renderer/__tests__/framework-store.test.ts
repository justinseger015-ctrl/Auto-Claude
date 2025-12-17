/**
 * Unit tests for Framework Store
 * Tests Zustand store for planning framework state management
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useFrameworkStore, getSelectedFramework, setFramework } from '../stores/framework-store';

describe('Framework Store', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useFrameworkStore.setState({
      selectedFramework: 'bmad'
    });
  });

  describe('initial state', () => {
    it('should default to bmad framework', () => {
      expect(useFrameworkStore.getState().selectedFramework).toBe('bmad');
    });
  });

  describe('setFramework', () => {
    it('should set framework to native', () => {
      useFrameworkStore.getState().setFramework('native');

      expect(useFrameworkStore.getState().selectedFramework).toBe('native');
    });

    it('should set framework to bmad', () => {
      // First change to native
      useFrameworkStore.getState().setFramework('native');
      // Then change back to bmad
      useFrameworkStore.getState().setFramework('bmad');

      expect(useFrameworkStore.getState().selectedFramework).toBe('bmad');
    });
  });

  describe('getSelectedFramework helper', () => {
    it('should return current framework value', () => {
      expect(getSelectedFramework()).toBe('bmad');

      useFrameworkStore.getState().setFramework('native');
      expect(getSelectedFramework()).toBe('native');
    });
  });

  describe('setFramework helper', () => {
    it('should update framework via helper function', () => {
      setFramework('native');

      expect(useFrameworkStore.getState().selectedFramework).toBe('native');
    });
  });
});
