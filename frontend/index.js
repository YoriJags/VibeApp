import { registerWidgetTaskHandler } from 'react-native-android-widget';
import { widgetTaskHandler } from './src/widgets/widget-task-handler';

// Widget rendering runs headless (no UI tree), so register before the router.
registerWidgetTaskHandler(widgetTaskHandler);

import 'expo-router/entry';
