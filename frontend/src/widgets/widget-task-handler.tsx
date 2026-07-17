import React from 'react';
import type { WidgetTaskHandlerProps } from 'react-native-android-widget';
import { CityPulseWidget, CityPulseData } from './CityPulseWidget';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://vibeapp-production-1835.up.railway.app';

async function fetchPulse(): Promise<CityPulseData | null> {
  try {
    const r = await fetch(`${API_URL}/api/city-pulse/lagos`);
    if (!r.ok) return null;
    const p = await r.json();
    return {
      score: p.pulse_score ?? 0,
      label: p.pulse_label ?? 'QUIET',
      trending: p.trending_venue ? `▲ ${p.trending_venue.name}` : '',
      updated: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    };
  } catch {
    return null;
  }
}

export async function widgetTaskHandler(props: WidgetTaskHandlerProps) {
  switch (props.widgetAction) {
    case 'WIDGET_ADDED':
    case 'WIDGET_UPDATE':
    case 'WIDGET_RESIZED': {
      const data = await fetchPulse();
      props.renderWidget(<CityPulseWidget data={data} />);
      break;
    }
    default:
      break;
  }
}
