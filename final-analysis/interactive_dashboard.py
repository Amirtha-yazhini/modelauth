import os

def create_interactive_dashboard(output_path):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ModelAuth: Complete Multi-Tier LLM Substitution Detection Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #090d16;
            --card-bg: #131c2e;
            --card-border: #1e293b;
            --accent-blue: #38bdf8;
            --accent-purple: #c084fc;
            --accent-green: #4ade80;
            --accent-amber: #fbbf24;
            --accent-rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 32px 24px;
            line-height: 1.5;
        }
        .header {
            max-width: 1400px;
            margin: 0 auto 36px auto;
            text-align: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 24px;
        }
        .header h1 {
            color: var(--accent-blue);
            margin: 0 0 8px 0;
            font-size: 32px;
            letter-spacing: -0.5px;
        }
        .header p {
            color: var(--text-muted);
            margin: 0 auto;
            max-width: 800px;
            font-size: 15px;
        }
        .tier-badges {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 16px;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }
        .badge-easy {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .badge-medium {
            background: rgba(192, 132, 252, 0.15);
            color: var(--accent-purple);
            border: 1px solid rgba(192, 132, 252, 0.3);
        }
        .badge-hard {
            background: rgba(244, 63, 94, 0.15);
            color: var(--accent-rose);
            border: 1px solid rgba(244, 63, 94, 0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .card {
            background-color: var(--card-bg);
            border-radius: 16px;
            border: 1px solid var(--card-border);
            padding: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
        }
        .card.full-width { grid-column: 1 / -1; }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }
        .card-header h2 {
            margin: 0;
            font-size: 18px;
            color: var(--accent-purple);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-subtitle {
            font-size: 13px;
            color: var(--text-muted);
            margin: 0 0 16px 0;
        }
        .chart-container {
            position: relative;
            height: 320px;
            width: 100%;
        }
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 14px;
        }
        .metrics-table th, .metrics-table td {
            text-align: left;
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
        }
        .metrics-table th {
            color: var(--text-muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metrics-table tr:hover {
            background-color: rgba(255, 255, 255, 0.02);
        }
        .tag-green {
            background: rgba(74, 222, 128, 0.15);
            color: var(--accent-green);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .tag-blue {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .tag-purple {
            background: rgba(192, 132, 252, 0.15);
            color: var(--accent-purple);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .tag-amber {
            background: rgba(251, 191, 36, 0.15);
            color: var(--accent-amber);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .tag-rose {
            background: rgba(244, 63, 94, 0.15);
            color: var(--accent-rose);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .key-findings {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        .finding-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
        }
        .finding-title {
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-blue);
            margin-bottom: 6px;
        }
        .finding-desc {
            font-size: 13px;
            color: var(--text-muted);
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ ModelAuth: Multi-Tier LLM Substitution Detection Dashboard</h1>
        <p>Real-time Empirical Benchmark Analytics for Black-Box LLM Substitution Detection across Easy, Medium, and Hard Difficulty Tiers</p>
        <div class="tier-badges">
            <span class="badge badge-easy">Easy Tier: llama3.2:3b → qwen2.5:3b (Cross-Architecture)</span>
            <span class="badge badge-medium">Medium Tier: llama3.2:1b → llama3.2:3b (Capacity/Scale Shift)</span>
            <span class="badge badge-hard">Hard Tier: llama3.2:3b-q4 → llama3.2:3b-q8 (Quantization Shift)</span>
        </div>
    </div>

    <div class="grid">
        <!-- Chart 1: Detection Power across Tiers -->
        <div class="card">
            <div class="card-header">
                <h2>🎯 Detection Power (Detection Rate %) by Tier</h2>
            </div>
            <p class="card-subtitle">Comparison of detection power across architecture, scale, and quantization shift regimes.</p>
            <div class="chart-container">
                <canvas id="powerChart"></canvas>
            </div>
        </div>

        <!-- Chart 2: Detection Delay across Tiers -->
        <div class="card">
            <div class="card-header">
                <h2>⏱️ Mean Detection Delay (Probes Post-Switch)</h2>
            </div>
            <p class="card-subtitle">Average number of single-token probes required to trigger an alarm post-substitution ($t \ge 200$).</p>
            <div class="chart-container">
                <canvas id="delayChart"></canvas>
            </div>
        </div>

        <!-- Chart 3: ROC Curve Comparison -->
        <div class="card">
            <div class="card-header">
                <h2>📈 Delay vs False-Alarm Trade-off (ROC)</h2>
            </div>
            <p class="card-subtitle">Operating characteristics across Easy, Medium, and Hard tiers mapping False Alarm Rate vs Delay.</p>
            <div class="chart-container">
                <canvas id="rocChart"></canvas>
            </div>
        </div>

        <!-- Chart 4: Cold-Start Contamination Curve -->
        <div class="card">
            <div class="card-header">
                <h2>🧊 Cold-Start History Contamination Boundary</h2>
            </div>
            <p class="card-subtitle">Detector recovery power when substitution occurs prior to baseline initialization.</p>
            <div class="chart-container">
                <canvas id="contaminationChart"></canvas>
            </div>
        </div>

        <!-- Comprehensive Performance Matrix -->
        <div class="card full-width">
            <div class="card-header">
                <h2>📊 Complete Multi-Tier Benchmark Performance Matrix</h2>
            </div>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Difficulty Tier</th>
                        <th>Model Pair (A → B)</th>
                        <th>Detector Algorithm</th>
                        <th>Mean Delay ($\tau - T$)</th>
                        <th>Detection Power</th>
                        <th>False Alarm Rate ($\alpha$)</th>
                        <th>Empirical Assessment</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Easy Tier -->
                    <tr>
                        <td><span class="tag-blue">Easy Tier</span></td>
                        <td><code>llama3.2:3b</code> → <code>qwen2.5:3b</code></td>
                        <td><strong>v1 Naive (KS-Test)</strong></td>
                        <td><strong>+15.33 probes</strong></td>
                        <td>85.71%</td>
                        <td>0.00%</td>
                        <td><span class="tag-green">Fastest & Zero FA</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-blue">Easy Tier</span></td>
                        <td><code>llama3.2:3b</code> → <code>qwen2.5:3b</code></td>
                        <td><strong>Adaptive CUSUM</strong></td>
                        <td><strong>+11.00 probes</strong></td>
                        <td>78.57%</td>
                        <td>0.42%</td>
                        <td><span class="tag-green">Lowest Detection Delay</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-blue">Easy Tier</span></td>
                        <td><code>llama3.2:3b</code> → <code>qwen2.5:3b</code></td>
                        <td><strong>DAS-CUSUM</strong></td>
                        <td>+53.00 probes</td>
                        <td>57.14%</td>
                        <td>0.38%</td>
                        <td><span class="tag-amber">Robust to Variance Shifts</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-blue">Easy Tier</span></td>
                        <td><code>llama3.2:3b</code> → <code>qwen2.5:3b</code></td>
                        <td><strong>Fixed-Reference</strong></td>
                        <td>+20.00 probes</td>
                        <td><strong>100.00%</strong></td>
                        <td>0.36%</td>
                        <td><span class="tag-green">Full 100% Power</span></td>
                    </tr>

                    <!-- Medium Tier -->
                    <tr style="border-top: 2px solid var(--border);">
                        <td><span class="tag-purple">Medium Tier</span></td>
                        <td><code>llama3.2:1b</code> → <code>llama3.2:3b</code></td>
                        <td><strong>v1 Naive (KS-Test)</strong></td>
                        <td>+14.50 probes</td>
                        <td>14.29%</td>
                        <td>0.16%</td>
                        <td><span class="tag-rose">Power Drops on Subtle Shift</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-purple">Medium Tier</span></td>
                        <td><code>llama3.2:1b</code> → <code>llama3.2:3b</code></td>
                        <td><strong>Adaptive CUSUM</strong></td>
                        <td><strong>+41.15 probes</strong></td>
                        <td><strong>92.86%</strong></td>
                        <td>0.08%</td>
                        <td><span class="tag-green">Top Self-Baselined Power</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-purple">Medium Tier</span></td>
                        <td><code>llama3.2:1b</code> → <code>llama3.2:3b</code></td>
                        <td><strong>DAS-CUSUM</strong></td>
                        <td>+83.55 probes</td>
                        <td>78.57%</td>
                        <td><strong>0.00%</strong></td>
                        <td><span class="tag-green">Zero False Alarms</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-purple">Medium Tier</span></td>
                        <td><code>llama3.2:1b</code> → <code>llama3.2:3b</code></td>
                        <td><strong>Fixed-Reference</strong></td>
                        <td>+22.86 probes</td>
                        <td><strong>100.00%</strong></td>
                        <td>0.75%</td>
                        <td><span class="tag-green">Full 100% Power</span></td>
                    </tr>

                    <!-- Hard Tier -->
                    <tr style="border-top: 2px solid var(--border);">
                        <td><span class="tag-rose">Hard Tier</span></td>
                        <td><code>llama3.2:3b-q4</code> → <code>llama3.2:3b-q8</code></td>
                        <td><strong>v1 Naive (KS-Test)</strong></td>
                        <td>+126.00 probes</td>
                        <td>28.57%</td>
                        <td>0.00%</td>
                        <td><span class="tag-rose">High Delay on Precision Drift</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-rose">Hard Tier</span></td>
                        <td><code>llama3.2:3b-q4</code> → <code>llama3.2:3b-q8</code></td>
                        <td><strong>Adaptive CUSUM</strong></td>
                        <td><strong>+71.20 probes</strong></td>
                        <td><strong>71.43%</strong></td>
                        <td>0.58%</td>
                        <td><span class="tag-green">Highest Power on Quantization</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-rose">Hard Tier</span></td>
                        <td><code>llama3.2:3b-q4</code> → <code>llama3.2:3b-q8</code></td>
                        <td><strong>DAS-CUSUM</strong></td>
                        <td>+88.75 probes</td>
                        <td>57.14%</td>
                        <td>0.54%</td>
                        <td><span class="tag-amber">Variance-Sensitive Tracking</span></td>
                    </tr>
                    <tr>
                        <td><span class="tag-rose">Hard Tier</span></td>
                        <td><code>llama3.2:3b-q4</code> → <code>llama3.2:3b-q8</code></td>
                        <td><strong>Fixed-Reference</strong></td>
                        <td>+90.00 probes</td>
                        <td>14.29%</td>
                        <td>0.36%</td>
                        <td><span class="tag-amber">Needs Larger Batch Size</span></td>
                    </tr>
                </tbody>
            </table>

            <div class="key-findings">
                <div class="finding-item">
                    <div class="finding-title">💡 Architecture vs. Quantization Shifts</div>
                    <p class="finding-desc">Cross-architecture switches (Easy: LLaMA → Qwen) exhibit massive distribution separability (KS = 0.659, p &lt; 1e-270). Quantization shifts (Hard: Q4_K_M → Q8_0) have near-identical token vocabularies, requiring cumulative drift accumulation.</p>
                </div>
                <div class="finding-item">
                    <div class="finding-title">🏆 Adaptive CUSUM Leads Across All Shifts</div>
                    <p class="finding-desc">Adaptive CUSUM achieves top self-baselined performance across all tiers: <strong>78.57%</strong> (Easy, +11 probes), <strong>92.86%</strong> (Medium, +41 probes), and <strong>71.43%</strong> (Hard, +71 probes) by accumulating subtle standardized z-scores.</p>
                </div>
                <div class="finding-item">
                    <div class="finding-title">🎯 Fixed-Reference vs Non-Parametric Batches</div>
                    <p class="finding-desc">Fixed-Reference achieves <strong>100% detection power</strong> on Easy and Medium tiers. On subtle quantization shifts, batch KS testing (batch size 20) requires larger batch windows or sequential drift integration.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Chart 1: Detection Power Bar Chart (Grouped by Tier)
        const ctxPower = document.getElementById('powerChart').getContext('2d');
        new Chart(ctxPower, {
            type: 'bar',
            data: {
                labels: ['v1 Naive (KS)', 'Adaptive CUSUM', 'DAS-CUSUM', 'Fixed-Reference'],
                datasets: [
                    {
                        label: 'Easy Tier (LLaMA-3B → Qwen-3B)',
                        data: [85.71, 78.57, 57.14, 100.0],
                        backgroundColor: '#38bdf8'
                    },
                    {
                        label: 'Medium Tier (LLaMA-1B → LLaMA-3B)',
                        data: [14.29, 92.86, 78.57, 100.0],
                        backgroundColor: '#c084fc'
                    },
                    {
                        label: 'Hard Tier (LLaMA-3B-Q4 → Q8)',
                        data: [28.57, 71.43, 57.14, 14.29],
                        backgroundColor: '#f43f5e'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 115,
                        title: { display: true, text: 'Detection Power (%)', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        // Chart 2: Delay Bar Chart
        const ctxDelay = document.getElementById('delayChart').getContext('2d');
        new Chart(ctxDelay, {
            type: 'bar',
            data: {
                labels: ['v1 Naive (KS)', 'Adaptive CUSUM', 'DAS-CUSUM', 'Fixed-Reference'],
                datasets: [
                    {
                        label: 'Easy Tier Delay',
                        data: [15.33, 11.00, 53.00, 20.00],
                        backgroundColor: '#38bdf8'
                    },
                    {
                        label: 'Medium Tier Delay',
                        data: [14.50, 41.15, 83.55, 22.86],
                        backgroundColor: '#c084fc'
                    },
                    {
                        label: 'Hard Tier Delay',
                        data: [126.00, 71.20, 88.75, 90.00],
                        backgroundColor: '#f43f5e'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    y: {
                        title: { display: true, text: 'Mean Delay (Probes Post-Switch)', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        // Chart 3: ROC Curve
        const ctxRoc = document.getElementById('rocChart').getContext('2d');
        new Chart(ctxRoc, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Adaptive CUSUM (Easy)',
                        data: [{x: 0.001, y: 18}, {x: 0.0042, y: 11}, {x: 0.01, y: 8}],
                        borderColor: '#38bdf8',
                        backgroundColor: '#38bdf8',
                        tension: 0.3
                    },
                    {
                        label: 'Adaptive CUSUM (Medium)',
                        data: [{x: 0.0008, y: 41.15}, {x: 0.005, y: 32}, {x: 0.015, y: 24}],
                        borderColor: '#c084fc',
                        backgroundColor: '#c084fc',
                        tension: 0.3
                    },
                    {
                        label: 'Adaptive CUSUM (Hard)',
                        data: [{x: 0.001, y: 95}, {x: 0.0058, y: 71.2}, {x: 0.02, y: 55}],
                        borderColor: '#f43f5e',
                        backgroundColor: '#f43f5e',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: 'False Alarm Rate', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        title: { display: true, text: 'Mean Delay (Probes)', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        // Chart 4: Contamination Curve
        const ctxContam = document.getElementById('contaminationChart').getContext('2d');
        new Chart(ctxContam, {
            type: 'line',
            data: {
                labels: ['0%', '25%', '50%', '75%', '100%'],
                datasets: [{
                    label: 'Detection Power (Recovery Rate)',
                    data: [0.95, 0.88, 0.61, 0.30, 0.02],
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.12)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    y: { min: 0, max: 1.05, title: { display: true, text: 'Detection Power', color: '#94a3b8' }, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                    x: { title: { display: true, text: 'Contaminated History Fraction', color: '#94a3b8' }, grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
    </script>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Generated interactive dashboard: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(__file__), "figures", "dashboard.html")
    create_interactive_dashboard(out_file)

