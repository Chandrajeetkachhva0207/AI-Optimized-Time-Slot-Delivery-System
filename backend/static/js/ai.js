const AI_API_BASE = '/api/delivery';

async function optimizeRouteViaApi({ source, destination, depot = { lat: 19.076, lon: 72.8777 }, stops = [] }) {
  const body = source && destination ? { source, destination } : { depot, stops };
  const response = await fetch(`${AI_API_BASE}/ai/optimize-route`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error || 'Route optimization failed');
  }
  return data;
}

function formatRouteResult(data) {
  const routeStops = Array.isArray(data.ordered_stops) && data.ordered_stops.length ? data.ordered_stops : (Array.isArray(data.stops) ? data.stops : []);
  const lines = [];
  if (data.driver_name || data.driver_id) {
    lines.push(`Driver: ${data.driver_name || `#${data.driver_id}`}`);
  }
  if (data.traffic) {
    lines.push(`Traffic: ${data.traffic}`);
  }
  if (data.distance) {
    lines.push(`Distance: ${data.distance}`);
  }
  if (data.eta) {
    lines.push(`Estimated time: ${data.eta}`);
  }
  if (typeof data.route_score === 'number') {
    lines.push(`Route score: ${data.route_score}`);
  }
  if (routeStops.length) {
    lines.push(`Route path: ${routeStops.map((stop, idx) => stop.label || stop.id || `Stop ${idx + 1}`).join(' → ')}`);
  }
  if (Array.isArray(data.legs) && data.legs.length) {
    lines.push('');
    lines.push('Leg details:');
    data.legs.forEach((leg, idx) => {
      lines.push(`  ${idx + 1}. ${leg.km.toFixed(2)} km from [${leg.from[0].toFixed(4)}, ${leg.from[1].toFixed(4)}] to [${leg.to[0].toFixed(4)}, ${leg.to[1].toFixed(4)}]`);
    });
  }
  return lines.join('\n');
}
