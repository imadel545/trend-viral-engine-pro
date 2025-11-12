/**
 * Custom Hooks - Advanced UX Utilities
 * 
 * Hooks réutilisables pour fonctionnalités avancées :
 * - useMediaQuery (responsive)
 * - useDebounce (performance)
 * - useLocalStorage (persistence)
 * - useIntersectionObserver (lazy loading)
 * - useCopyToClipboard (UX)
 * - useKeyPress (keyboard shortcuts)
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// useMediaQuery - Responsive Design
// ============================================================================

export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(() => {
        if (typeof window !== 'undefined') {
            return window.matchMedia(query).matches;
        }
        return false;
    });

    useEffect(() => {
        const media = window.matchMedia(query);
        const listener = () => setMatches(media.matches);

        media.addEventListener('change', listener);

        return () => media.removeEventListener('change', listener);
    }, [query]);

    return matches;
}

// Breakpoint hooks
export const useIsMobile = () => useMediaQuery('(max-width: 768px)');
export const useIsTablet = () => useMediaQuery('(min-width: 768px) and (max-width: 1024px)');
export const useIsDesktop = () => useMediaQuery('(min-width: 1024px)');

// ============================================================================
// useDebounce - Performance Optimization
// ============================================================================

export function useDebounce<T>(value: T, delay: number = 500): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

// ============================================================================
// useLocalStorage - Persistence
// ============================================================================

export function useLocalStorage<T>(
    key: string,
    initialValue: T
): [T, (value: T | ((val: T) => T)) => void] {
    // State to store our value
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') {
            return initialValue;
        }

        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(`Error reading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    // Return a wrapped version of useState's setter function that persists
    const setValue = (value: T | ((val: T) => T)) => {
        try {
            const valueToStore =
                value instanceof Function ? value(storedValue) : value;

            setStoredValue(valueToStore);

            if (typeof window !== 'undefined') {
                window.localStorage.setItem(key, JSON.stringify(valueToStore));
            }
        } catch (error) {
            console.error(`Error setting localStorage key "${key}":`, error);
        }
    };

    return [storedValue, setValue];
}

// ============================================================================
// useIntersectionObserver - Lazy Loading / Scroll Animations
// ============================================================================

export function useIntersectionObserver(
    elementRef: React.RefObject<Element>,
    {
        threshold = 0.1,
        root = null,
        rootMargin = '0px',
        freezeOnceVisible = false,
    }: {
        threshold?: number;
        root?: Element | null;
        rootMargin?: string;
        freezeOnceVisible?: boolean;
    } = {}
): IntersectionObserverEntry | undefined {
    const [entry, setEntry] = useState<IntersectionObserverEntry>();

    const frozen = entry?.isIntersecting && freezeOnceVisible;

    const updateEntry = ([entry]: IntersectionObserverEntry[]): void => {
        setEntry(entry);
    };

    useEffect(() => {
        const node = elementRef?.current;
        const hasIOSupport = !!window.IntersectionObserver;

        if (!hasIOSupport || frozen || !node) return;

        const observerParams = { threshold, root, rootMargin };
        const observer = new IntersectionObserver(updateEntry, observerParams);

        observer.observe(node);

        return () => observer.disconnect();
    }, [elementRef, threshold, root, rootMargin, frozen]);

    return entry;
}

// ============================================================================
// useCopyToClipboard - UX Enhancement
// ============================================================================

export function useCopyToClipboard(): [
    boolean,
    (text: string) => Promise<void>
] {
    const [copied, setCopied] = useState(false);

    const copy = useCallback(async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);

            // Reset after 2 seconds
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            setCopied(false);
        }
    }, []);

    return [copied, copy];
}

// ============================================================================
// useKeyPress - Keyboard Shortcuts
// ============================================================================

export function useKeyPress(targetKey: string): boolean {
    const [keyPressed, setKeyPressed] = useState(false);

    useEffect(() => {
        const downHandler = ({ key }: KeyboardEvent) => {
            if (key === targetKey) {
                setKeyPressed(true);
            }
        };

        const upHandler = ({ key }: KeyboardEvent) => {
            if (key === targetKey) {
                setKeyPressed(false);
            }
        };

        window.addEventListener('keydown', downHandler);
        window.addEventListener('keyup', upHandler);

        return () => {
            window.removeEventListener('keydown', downHandler);
            window.removeEventListener('keyup', upHandler);
        };
    }, [targetKey]);

    return keyPressed;
}

// ============================================================================
// useClickOutside - Modal/Dropdown Close
// ============================================================================

export function useClickOutside(
    ref: React.RefObject<HTMLElement>,
    handler: () => void
): void {
    useEffect(() => {
        const listener = (event: MouseEvent | TouchEvent) => {
            if (!ref.current || ref.current.contains(event.target as Node)) {
                return;
            }
            handler();
        };

        document.addEventListener('mousedown', listener);
        document.addEventListener('touchstart', listener);

        return () => {
            document.removeEventListener('mousedown', listener);
            document.removeEventListener('touchstart', listener);
        };
    }, [ref, handler]);
}

// ============================================================================
// useWindowSize - Responsive Utilities
// ============================================================================

interface WindowSize {
    width: number | undefined;
    height: number | undefined;
}

export function useWindowSize(): WindowSize {
    const [windowSize, setWindowSize] = useState<WindowSize>({
        width: undefined,
        height: undefined,
    });

    useEffect(() => {
        function handleResize() {
            setWindowSize({
                width: window.innerWidth,
                height: window.innerHeight,
            });
        }

        window.addEventListener('resize', handleResize);
        handleResize();

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return windowSize;
}

// ============================================================================
// useScrollPosition - Scroll Effects
// ============================================================================

export function useScrollPosition(): number {
    const [scrollPosition, setScrollPosition] = useState(0);

    useEffect(() => {
        const updatePosition = () => {
            setScrollPosition(window.scrollY);
        };

        window.addEventListener('scroll', updatePosition);
        updatePosition();

        return () => window.removeEventListener('scroll', updatePosition);
    }, []);

    return scrollPosition;
}

// ============================================================================
// useHover - Hover State
// ============================================================================

export function useHover<T extends HTMLElement = HTMLElement>(): [
    React.RefObject<T | null>,
    boolean
] {
    const [isHovered, setIsHovered] = useState(false);
    const ref = useRef<T | null>(null);

    useEffect(() => {
        const node = ref.current;
        if (!node) return;

        const handleMouseEnter = () => setIsHovered(true);
        const handleMouseLeave = () => setIsHovered(false);

        node.addEventListener('mouseenter', handleMouseEnter);
        node.addEventListener('mouseleave', handleMouseLeave);

        return () => {
            node.removeEventListener('mouseenter', handleMouseEnter);
            node.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, []);

    return [ref, isHovered];
}

// ============================================================================
// useToggle - Boolean State Toggle
// ============================================================================

export function useToggle(
    initialValue: boolean = false
): [boolean, () => void, (value: boolean) => void] {
    const [value, setValue] = useState(initialValue);

    const toggle = useCallback(() => {
        setValue((v) => !v);
    }, []);

    return [value, toggle, setValue];
}

// ============================================================================
// useInterval - Setinterval Hook
// ============================================================================

export function useInterval(callback: () => void, delay: number | null): void {
    const savedCallback = useRef(callback);

    useEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    useEffect(() => {
        if (delay === null) return;

        const id = setInterval(() => savedCallback.current(), delay);

        return () => clearInterval(id);
    }, [delay]);
}

// ============================================================================
// usePrevious - Previous Value
// ============================================================================

export function usePrevious<T>(value: T): T | undefined {
    const ref = useRef<T | undefined>(undefined);

    useEffect(() => {
        ref.current = value;
    });

    return ref.current;
}

// ============================================================================
// useAsync - Async Operations
// ============================================================================

interface AsyncState<T> {
    loading: boolean;
    error: Error | null;
    data: T | null;
}

export function useAsync<T>(
    asyncFunction: () => Promise<T>,
    immediate: boolean = true
): AsyncState<T> & { execute: () => Promise<void> } {
    const [state, setState] = useState<AsyncState<T>>({
        loading: immediate,
        error: null,
        data: null,
    });

    const execute = useCallback(async () => {
        setState({ loading: true, error: null, data: null });

        try {
            const data = await asyncFunction();
            setState({ loading: false, error: null, data });
        } catch (error) {
            setState({ loading: false, error: error as Error, data: null });
        }
    }, [asyncFunction]);

    useEffect(() => {
        if (immediate) {
            void execute();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [immediate]);

    return { ...state, execute };
}
