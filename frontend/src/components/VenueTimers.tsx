/**
 * VenueTimers — the two consumer countdowns.
 *
 *   PeakCountdown      "PEAKS IN ~40 MIN"     when should I be there
 *   FreshnessCountdown "READING EXPIRES 4:12" how long we still stand behind this
 *
 * Both stay silent when the backend has nothing honest to say: no forecast,
 * no timer. That is the creed applied to the clock.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const HEAT = {
  ember:    '#FF4D00',
  amber:    '#FFB300',
  whitehot: '#FFF3D6',
  smoke:    '#A89B8C',
  ash:      '#16110D',
  soot:     '#292019',
};

/** How long a reading is treated as current before it goes stale. */
export const READING_LIFESPAN_MINUTES = 15;

export interface PeakForecast {
  state: 'peaking_now' | 'building';
  minutes_to_peak: number;
  peak_hour: number;
  label: string;
}

export function PeakCountdown({ forecast }: { forecast?: PeakForecast | null }) {
  if (!forecast) return null;              // we do not know, so we say nothing
  const peaking = forecast.state === 'peaking_now';
  const color = peaking ? HEAT.whitehot : HEAT.amber;

  return (
    <View style={[styles.chip, { borderColor: color + '55' }]}>
      <Ionicons name={peaking ? 'flame' : 'time-outline'} size={13} color={color} />
      <Text style={[styles.chipLabel, { color }]}>{forecast.label}</Text>
      {!peaking && (
        <Text style={styles.chipSub}>
          {forecast.minutes_to_peak >= 60 ? 'get moving' : 'good time to leave'}
        </Text>
      )}
    </View>
  );
}

/**
 * Counts the current reading down to expiry, ticking every second.
 * `lastRatedMinsAgo` comes from the API at load; we advance it locally.
 */
export function FreshnessCountdown({ lastRatedMinsAgo }: { lastRatedMinsAgo?: number | null }) {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  useEffect(() => {
    if (lastRatedMinsAgo === null || lastRatedMinsAgo === undefined) {
      setSecondsLeft(null);
      return;
    }
    const total = Math.round((READING_LIFESPAN_MINUTES - lastRatedMinsAgo) * 60);
    setSecondsLeft(total);
    if (total <= 0) return;

    const t = setInterval(() => {
      setSecondsLeft(prev => (prev === null ? null : Math.max(0, prev - 1)));
    }, 1000);
    return () => clearInterval(t);
  }, [lastRatedMinsAgo]);

  if (secondsLeft === null) return null;

  if (secondsLeft <= 0) {
    return (
      <View style={styles.expiredRow}>
        <Ionicons name="alert-circle-outline" size={12} color={HEAT.smoke} />
        <Text style={styles.expiredText}>READING EXPIRED &middot; NEEDS A FRESH CHECK</Text>
      </View>
    );
  }

  const mm = Math.floor(secondsLeft / 60);
  const ss = String(secondsLeft % 60).padStart(2, '0');
  const urgent = secondsLeft < 180;

  return (
    <View style={styles.expiredRow}>
      <Ionicons name="hourglass-outline" size={12} color={urgent ? HEAT.ember : HEAT.smoke} />
      <Text style={[styles.expiredText, urgent && { color: HEAT.ember }]}>
        READING EXPIRES IN {mm}:{ss}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    alignSelf: 'flex-start',
    backgroundColor: HEAT.ash,
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  chipLabel: { fontSize: 12, fontWeight: '700', letterSpacing: 1.2 },
  chipSub:   { fontSize: 10, color: HEAT.smoke, letterSpacing: 0.6 },
  expiredRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  expiredText: { fontSize: 10, color: HEAT.smoke, letterSpacing: 1.1 },
});
