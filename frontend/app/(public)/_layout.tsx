/**
 * PUBLIC FLOOR - Layout
 * The Social Experience - Neon/Midnight Theme
 *
 * Navigation: Explore | Trending | Crew | Intel | Profile
 * Access: All users (default entry point)
 *
 * Features: Custom AnimatedTabBar with neon pink glow
 */
import React from 'react';
import { Tabs } from 'expo-router';
import { publicTheme } from '../../src/theme/floors';
import { AnimatedTabBar } from '../../src/components/AnimatedTabBar';
import { useVibeStore } from '../../src/store/vibeStore';

const { colors } = publicTheme;

const ALL_TABS = [
  { name: 'index',    label: 'Map',      icon: 'compass-outline' as const,      iconFocused: 'compass' as const },
  { name: 'trending', label: 'Tonight',  icon: 'flame-outline' as const,         iconFocused: 'flame' as const },
  { name: 'crew',     label: 'Crew',     icon: 'people-outline' as const,        iconFocused: 'people' as const },
  { name: 'intel',    label: 'Intel',    icon: 'sparkles-outline' as const,      iconFocused: 'sparkles' as const },
  { name: 'profile',  label: 'Profile',  icon: 'person-outline' as const,        iconFocused: 'person' as const },
];
// R0 launch surface: Map - Tonight - Profile (docs/LAUNCH_AUDIT.md)
const LAUNCH_TABS = ALL_TABS.filter(t => ['index', 'trending', 'profile'].includes(t.name));

export default function PublicLayout() {
  const launchMode = useVibeStore(s => s.launchMode);
  const tabs = launchMode ? LAUNCH_TABS : ALL_TABS;
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
      }}
      tabBar={(props) => (
        <AnimatedTabBar
          {...props}
          glowColor={colors.primary}
          inactiveColor={colors.text.muted}
          tabs={tabs}
        />
      )}
    >
      <Tabs.Screen name="index" />
      <Tabs.Screen name="trending" />
      <Tabs.Screen name="crew" options={launchMode ? { href: null } : {}} />
      <Tabs.Screen name="intel" options={launchMode ? { href: null } : {}} />
      <Tabs.Screen name="profile" />
      {/* Lobby kept as a push screen, not a tab — accessible from Profile */}
      <Tabs.Screen name="lobby" options={{ href: null }} />
    </Tabs>
  );
}
