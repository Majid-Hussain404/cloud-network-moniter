async function loadOverview() {
  const [overviewResponse, targetsResponse, metricsResponse, incidentsResponse] = await Promise.all([
    fetch('/api/overview'),
    fetch('/api/targets'),
    fetch('/api/system-metrics'),
    fetch('/api/incidents'),
  ]);
  if (!overviewResponse.ok || !targetsResponse.ok || !metricsResponse.ok || !incidentsResponse.ok) throw new Error('The API returned an error.');
  const data = await overviewResponse.json();
  const targets = await targetsResponse.json();
  const metrics = await metricsResponse.json();
  const incidents = await incidentsResponse.json();
  document.querySelector('#monitoring-status').textContent = data.monitoring_status;
  document.querySelector('#overview-message').textContent = data.message;
  document.querySelector('#targets-monitored').textContent = data.targets_monitored;
  document.querySelector('#healthy-targets').textContent = data.healthy_targets;
  document.querySelector('#active-alerts').textContent = data.active_alerts;
  document.querySelector('#cpu-percent').textContent = `${metrics.cpu_percent}%`;
  document.querySelector('#memory-percent').textContent = `${metrics.memory_percent}%`;
  document.querySelector('#uptime').textContent = formatUptime(metrics.uptime_seconds);
  document.querySelector('#bytes-received').textContent = formatBytes(metrics.bytes_received);
  renderIncidents(incidents);

  const targetPanel = document.querySelector('#targets .empty-state');
  if (targets.length > 0) {
    targetPanel.innerHTML = targets.map((target) => `
      <div class="target-row">
        <div><strong>${target.name}</strong><small>${target.target_type}: ${target.address}${target.port ? `:${target.port}` : ''}</small></div>
        ${renderTargetStatus(target.latest_result)}
      </div>
    `).join('');
    targetPanel.classList.add('target-list');
  }
}

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return `${days}d ${hours}h`;
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderIncidents(incidents) {
  const alertState = document.querySelector('#alerts .empty-state');
  if (incidents.length === 0) return;
  alertState.innerHTML = incidents.map((incident) => `
    <div class="incident-row">
      <strong>${incident.status === 'open' ? 'Open incident' : 'Resolved incident'}</strong>
      <span>${incident.reason}</span>
    </div>
  `).join('');
  alertState.classList.add('incident-list');
}

function renderTargetStatus(result) {
  if (!result) return '<span class="status-badge pending">Pending checks</span>';
  if (result.success) return `<span class="status-badge online">Online · ${result.response_time_ms} ms</span>`;
  return '<span class="status-badge offline">Offline</span>';
}

loadOverview().catch((error) => {
  document.querySelector('#monitoring-status').textContent = 'API unavailable';
  document.querySelector('#overview-message').textContent = error.message;
});
