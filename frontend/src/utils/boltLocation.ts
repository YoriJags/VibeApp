import * as Location from 'expo-location';

/**
 * Best-effort coordinates for bolt taps. The backend damps taps without
 * verified in-geofence coordinates (honest-scarcity surge policy), so we
 * attach the freshest position we can get without blocking the tap.
 * Returns null when permission is missing or no fix is available.
 */
export async function getBoltCoordinates(): Promise<{ lat: number; lng: number } | null> {
  try {
    const { status } = await Location.getForegroundPermissionsAsync();
    if (status !== 'granted') return null;
    const last = await Location.getLastKnownPositionAsync({ maxAge: 120_000 });
    const pos = last ?? await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    return { lat: pos.coords.latitude, lng: pos.coords.longitude };
  } catch {
    return null;
  }
}
