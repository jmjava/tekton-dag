/**
 * Re-export from the standalone @tekton-dag/baggage library.
 * Call install() — do not copy x-dev-session by hand.
 */
export {
  parseBaggage,
  mergeBaggage,
  serializeBaggage,
  createBaggageConfig,
  defaultConfig,
  createBaggageFetch,
  createAxiosInterceptor,
  adoptIncoming,
  install,
} from '@tekton-dag/baggage'
