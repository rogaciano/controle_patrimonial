"""Script to write clean dashboard.html template."""
import os

LB = '{'
RB = '}'
DB_L = '{{'
DB_R = '}}'
TAG_L = '{%'
TAG_R = '%}'

lines = []
lines.append(f"{TAG_L} extends 'base.html' {TAG_R}")
lines.append("")
lines.append(f"{TAG_L} block title {TAG_R}Dashboard - Controle Patrimonial{TAG_L} endblock {TAG_R}")
lines.append("")
lines.append(f"{TAG_L} block header {TAG_R}")
lines.append('<header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">')
lines.append('    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">')
lines.append('        <h2 class="text-xl font-bold text-slate-900 dark:text-white">Dashboard Patrimonial</h2>')
lines.append('        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Visao geral do patrimonio</p>')
lines.append('    </div>')
lines.append('</header>')
lines.append(f"{TAG_L} endblock {TAG_R}")
lines.append("")
lines.append(f"{TAG_L} block content {TAG_R}")
lines.append('<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">')

# KPI Cards
lines.append('    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">')

kpis = [
    ("Total de Ativos", f"{DB_L} total_ativos {DB_R}", "text-3xl", "primary", "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"),
    ("Valor Total", f"R$ {DB_L} valor_total|floatformat:2 {DB_R}", "text-2xl", "green", "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"),
    ("Movimentacoes Pendentes", f"{DB_L} movimentacoes_pendentes {DB_R}", "text-3xl", "yellow", "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"),
    ("Depreciacao Acumulada", f"R$ {DB_L} depreciacao_total|floatformat:2 {DB_R}", "text-2xl", "red", "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"),
]

for label, value, size, color, icon_path in kpis:
    lines.append('        <div class="card group hover:shadow-xl transition-all duration-300">')
    lines.append('            <div class="flex items-center justify-between">')
    lines.append('                <div>')
    lines.append(f'                    <p class="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>')
    lines.append(f'                    <p class="mt-2 {size} font-bold text-slate-900 dark:text-white">{value}</p>')
    lines.append('                </div>')
    lines.append(f'                <div class="w-12 h-12 rounded-xl bg-{color}-100 dark:bg-{color}-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">')
    lines.append(f'                    <svg class="w-6 h-6 text-{color}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{icon_path}" /></svg>')
    lines.append('                </div>')
    lines.append('            </div>')
    lines.append('        </div>')

lines.append('    </div>')

# Charts
lines.append('    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">')
lines.append('        <div class="card">')
lines.append('            <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Ativos por Status</h3>')
lines.append('            <div class="h-64"><canvas id="chart-status"></canvas></div>')
lines.append('        </div>')
lines.append('        <div class="card">')
lines.append('            <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Ativos por Categoria</h3>')
lines.append('            <div class="h-64"><canvas id="chart-categoria"></canvas></div>')
lines.append('        </div>')
lines.append('    </div>')

# Quick Actions
actions = [
    ("patrimonio:ativo-create", "primary", "M12 4v16m8-8H4", "Novo Ativo", "Cadastrar novo bem"),
    ("patrimonio:movimentacao-create", "yellow", "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4", "Nova Movimentacao", "Registrar transferencia"),
    ("patrimonio:depreciacao-processar", "red", "M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z", "Processar Depreciacao", "Calculo mensal em lote"),
]

lines.append('    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">')
for url_name, color, icon_path, title, desc in actions:
    lines.append(f'        <a href="{TAG_L} url \'{url_name}\' {TAG_R}" class="card hover:shadow-xl transition-all group text-center">')
    lines.append(f'            <div class="w-12 h-12 rounded-xl bg-{color}-100 dark:bg-{color}-900/30 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">')
    lines.append(f'                <svg class="w-6 h-6 text-{color}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{icon_path}" /></svg>')
    lines.append('            </div>')
    lines.append(f'            <h4 class="font-semibold text-slate-900 dark:text-white">{title}</h4>')
    lines.append(f'            <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">{desc}</p>')
    lines.append('        </a>')
lines.append('    </div>')

lines.append('</div>')
lines.append(f"{TAG_L} endblock {TAG_R}")
lines.append("")

# JS block
lines.append(f"{TAG_L} block extra_js {TAG_R}")
lines.append('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>')
lines.append('<script>')
lines.append("document.addEventListener('DOMContentLoaded', function() {")
lines.append("    var isDark = document.documentElement.classList.contains('dark');")
lines.append("    Chart.defaults.color = isDark ? '#94a3b8' : '#64748b';")
lines.append("    Chart.defaults.borderColor = isDark ? 'rgba(148,163,184,0.1)' : 'rgba(0,0,0,0.05)';")
lines.append(f"    var statusData = JSON.parse('{DB_L} status_data|escapejs {DB_R}');")
lines.append("    if (statusData.length && document.getElementById('chart-status')) {")
lines.append("        new Chart(document.getElementById('chart-status'), {")
lines.append("            type: 'doughnut',")
lines.append("            data: { labels: statusData.map(function(d){return d.label}), datasets: [{data: statusData.map(function(d){return d.count}), backgroundColor: ['#0ea5e9','#f59e0b','#ef4444','#10b981','#8b5cf6'], borderWidth: 0, borderRadius: 4}] },")
lines.append("            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } } } }")
lines.append("        });")
lines.append("    }")
lines.append(f"    var catData = JSON.parse('{DB_L} categoria_data|escapejs {DB_R}');")
lines.append("    if (catData.length && document.getElementById('chart-categoria')) {")
lines.append("        new Chart(document.getElementById('chart-categoria'), {")
lines.append("            type: 'bar',")
lines.append("            data: { labels: catData.map(function(d){return d.label}), datasets: [{label: 'Qtd', data: catData.map(function(d){return d.count}), backgroundColor: isDark ? 'rgba(14,165,233,0.6)' : 'rgba(14,165,233,0.8)', borderRadius: 8}] },")
lines.append("            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }")
lines.append("        });")
lines.append("    }")
lines.append("});")
lines.append("</script>")
lines.append(f"{TAG_L} endblock {TAG_R}")

target = r"E:\projetos\patrimonial_lucivaldo\apps\patrimonio\templates\patrimonio\dashboard.html"
with open(target, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print(f"Written {len(lines)} lines to {target}")
