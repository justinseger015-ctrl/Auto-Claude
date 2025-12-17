/**
 * Unit tests for GlossaryContext
 * Tests provider, hook, and framework-glossary mapping
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useFrameworkStore } from '../stores/framework-store';
import { getGlossary, BMAD_GLOSSARY, NATIVE_GLOSSARY } from '../../shared/types/glossary';
import type { PlanningFramework } from '../../shared/types';

describe('Glossary System', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useFrameworkStore.setState({
      selectedFramework: 'bmad'
    });
  });

  describe('getGlossary function', () => {
    it('should return BMAD glossary for bmad framework', () => {
      const glossary = getGlossary('bmad');
      expect(glossary).toBe(BMAD_GLOSSARY);
    });

    it('should return NATIVE glossary for native framework', () => {
      const glossary = getGlossary('native');
      expect(glossary).toBe(NATIVE_GLOSSARY);
    });
  });

  describe('BMAD_GLOSSARY', () => {
    it('should have correct terminology', () => {
      expect(BMAD_GLOSSARY.workUnit).toBe('Epic');
      expect(BMAD_GLOSSARY.task).toBe('Story');
      expect(BMAD_GLOSSARY.checkpoint).toBe('Task');
      expect(BMAD_GLOSSARY.planningPhase).toBe('Solutioning');
    });

    it('should have correct plural forms', () => {
      expect(BMAD_GLOSSARY.workUnits).toBe('Epics');
      expect(BMAD_GLOSSARY.tasks).toBe('Stories');
      expect(BMAD_GLOSSARY.checkpoints).toBe('Tasks');
    });
  });

  describe('NATIVE_GLOSSARY', () => {
    it('should have correct terminology', () => {
      expect(NATIVE_GLOSSARY.workUnit).toBe('Phase');
      expect(NATIVE_GLOSSARY.task).toBe('Subtask');
      expect(NATIVE_GLOSSARY.checkpoint).toBe('Verification');
      expect(NATIVE_GLOSSARY.planningPhase).toBe('Spec Creation');
    });

    it('should have correct plural forms', () => {
      expect(NATIVE_GLOSSARY.workUnits).toBe('Phases');
      expect(NATIVE_GLOSSARY.tasks).toBe('Subtasks');
      expect(NATIVE_GLOSSARY.checkpoints).toBe('Verifications');
    });
  });

  describe('Framework Store Integration', () => {
    it('should get correct glossary based on store state', () => {
      useFrameworkStore.setState({ selectedFramework: 'bmad' });
      const bmadGlossary = getGlossary(useFrameworkStore.getState().selectedFramework);
      expect(bmadGlossary.workUnit).toBe('Epic');

      useFrameworkStore.setState({ selectedFramework: 'native' });
      const nativeGlossary = getGlossary(useFrameworkStore.getState().selectedFramework);
      expect(nativeGlossary.workUnit).toBe('Phase');
    });

    it('should update glossary when framework changes', () => {
      // Start with bmad
      expect(useFrameworkStore.getState().selectedFramework).toBe('bmad');
      let glossary = getGlossary(useFrameworkStore.getState().selectedFramework);
      expect(glossary.task).toBe('Story');

      // Change to native
      useFrameworkStore.getState().setFramework('native');
      glossary = getGlossary(useFrameworkStore.getState().selectedFramework);
      expect(glossary.task).toBe('Subtask');
    });
  });

  describe('Glossary Type Safety', () => {
    it('should have all required properties', () => {
      const requiredKeys = [
        'workUnit',
        'task',
        'checkpoint',
        'planningPhase',
        'workUnits',
        'tasks',
        'checkpoints'
      ];

      for (const key of requiredKeys) {
        expect(BMAD_GLOSSARY).toHaveProperty(key);
        expect(NATIVE_GLOSSARY).toHaveProperty(key);
      }
    });

    it('should only return string values', () => {
      const checkGlossaryValues = (glossary: typeof BMAD_GLOSSARY) => {
        for (const value of Object.values(glossary)) {
          expect(typeof value).toBe('string');
        }
      };

      checkGlossaryValues(BMAD_GLOSSARY);
      checkGlossaryValues(NATIVE_GLOSSARY);
    });
  });
});
