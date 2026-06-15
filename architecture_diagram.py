# ============================================================
# FILE: architecture_diagram.py
# PURPOSE: Generate a professional architecture diagram
#          saved as architecture.png for the README
# ============================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')

# ── Colour palette ───────────────────────────────────────────
COLORS = {
    'posthog':    '#F97316',
    'supabase':   '#3ECF8E',
    'python':     '#3B82F6',
    'rag':        '#8B5CF6',
    'llm':        '#EC4899',
    'n8n':        '#F59E0B',
    'delivery':   '#10B981',
    'actions':    '#6366F1',
    'text':       '#F8FAFC',
    'subtext':    '#94A3B8',
    'arrow':      '#475569',
    'bg_card':    '#1E293B',
    'border':     '#334155',
}

def draw_card(ax, x, y, w, h, title, subtitle, color, emoji=''):
    card = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.05",
        facecolor=COLORS['bg_card'],
        edgecolor=color,
        linewidth=2.5,
        zorder=3
    )
    ax.add_patch(card)

    # Colour bar at top of card
    bar = FancyBboxPatch(
        (x, y + h - 0.22), w, 0.22,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor=color,
        linewidth=0,
        zorder=4
    )
    ax.add_patch(bar)

    ax.text(x + w/2, y + h - 0.08,
            f'{emoji} {title}',
            ha='center', va='center',
            fontsize=8.5, fontweight='bold',
            color='white', zorder=5)

    for i, line in enumerate(subtitle.split('\n')):
        ax.text(x + w/2, y + h - 0.55 - (i * 0.32),
                line,
                ha='center', va='center',
                fontsize=7, color=COLORS['subtext'],
                zorder=5)

def draw_arrow(ax, x1, y1, x2, y2, color='#475569'):
    ax.annotate('',
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle='->', color=color,
            lw=1.8, connectionstyle='arc3,rad=0.0'
        ),
        zorder=2
    )

# ── Title ─────────────────────────────────────────────────────
ax.text(10, 13.4,
        'LLM-Powered Customer Journey Orchestration Engine',
        ha='center', va='center',
        fontsize=16, fontweight='bold',
        color=COLORS['text'])

ax.text(10, 13.0,
        'PostHog → State Machine → RAG + LLaMA 3.3 70B → n8n → Email / Push / In-App',
        ha='center', va='center',
        fontsize=9, color=COLORS['subtext'])

# ── Row 1: Data Sources ───────────────────────────────────────
draw_card(ax, 0.3, 10.5, 3.2, 1.8,
          'PostHog', 'Real-time event\ntracking & analytics\n10 journey events',
          COLORS['posthog'], '📡')

draw_card(ax, 4.0, 10.5, 3.2, 1.8,
          'Supabase', 'PostgreSQL + pgvector\n7 tables\nAudit trail',
          COLORS['supabase'], '🗄️')

draw_card(ax, 7.7, 10.5, 3.2, 1.8,
          'GitHub Actions', 'Hourly cron\n48h outcome check\nWeekly RAG reindex',
          COLORS['actions'], '⚙️')

draw_card(ax, 11.4, 10.5, 3.2, 1.8,
          'Config Layer', 'journey_states.yml\ntrigger_rules.yml\nchannel_rules.yml',
          COLORS['python'], '📋')

draw_card(ax, 15.1, 10.5, 4.5, 1.8,
          'Knowledge Base', 'past_campaigns.csv\nbrand_voice.md\nuser_segments.md',
          COLORS['rag'], '📚')

# ── Row 2: State Machine ──────────────────────────────────────
draw_card(ax, 1.5, 7.8, 5.5, 1.9,
          'Journey State Machine',
          '7 states: NEW_SIGNUP → ACTIVATING → ACTIVATED\nRETAINED → CHURN_RISK → CHURNED → EXPANDING\nEvaluates PostHog events every hour',
          COLORS['python'], '🧠')

draw_card(ax, 8.2, 7.8, 5.0, 1.9,
          'Trigger Detector',
          '17 trigger types\nDeduplication logic\nWrites to journey_triggers table',
          COLORS['python'], '🎯')

draw_card(ax, 14.2, 7.8, 5.3, 1.9,
          'RAG Indexer',
          'sentence-transformers\nall-MiniLM-L6-v2\n45 chunks → VECTOR(384)',
          COLORS['rag'], '🔢')

# ── Row 3: AI Agent ───────────────────────────────────────────
draw_card(ax, 1.5, 5.0, 3.8, 2.0,
          'LangChain Agent',
          'Reads unprocessed triggers\nOrchestrates RAG + LLM\nLogs full reasoning chain',
          COLORS['python'], '🤖')

draw_card(ax, 6.2, 5.0, 3.8, 2.0,
          'RAG Retriever',
          'pgvector similarity search\nTop-5 relevant chunks\nCosine similarity scoring',
          COLORS['rag'], '🔍')

draw_card(ax, 11.0, 5.0, 3.8, 2.0,
          'LLaMA 3.3 70B',
          'Groq API (FREE)\nStructured JSON output\nChannel + reasoning',
          COLORS['llm'], '✨')

draw_card(ax, 15.8, 5.0, 3.7, 2.0,
          'Agent Decisions',
          'Full prompt logged\nLLM response stored\nReasoning auditable',
          COLORS['supabase'], '📝')

# ── Row 4: Delivery ───────────────────────────────────────────
draw_card(ax, 1.5, 2.2, 3.5, 2.0,
          'n8n Workflow',
          'Webhook receiver\nChannel router (Switch)\nMulti-channel delivery',
          COLORS['n8n'], '🔄')

draw_card(ax, 6.2, 2.2, 3.2, 2.0,
          'Brevo Email',
          'Personalised subject\n150-200 word body\nDelivered & tracked',
          COLORS['delivery'], '📧')

draw_card(ax, 10.5, 2.2, 3.2, 2.0,
          'OneSignal Push',
          'Max 100 characters\nUser-targeted\nCTR tracked',
          COLORS['delivery'], '📱')

draw_card(ax, 14.8, 2.2, 3.2, 2.0,
          'PostHog In-App',
          'Feature flag tooltip\nMax 60 characters\nIn-session delivery',
          COLORS['delivery'], '💬')

# ── Row 5: Outcomes ───────────────────────────────────────────
draw_card(ax, 4.5, 0.2, 5.0, 1.5,
          'Outcome Tracker',
          'Opens · Clicks · Conversions → message_outcomes table',
          COLORS['posthog'], '📊')

draw_card(ax, 10.5, 0.2, 5.0, 1.5,
          'Self-Improving Loop',
          'Performance data → RAG reindex → smarter messages',
          COLORS['rag'], '🔁')

# ── Arrows ────────────────────────────────────────────────────
# PostHog → State Machine
draw_arrow(ax, 1.9, 10.5, 2.8, 9.7, COLORS['posthog'])
# Supabase → State Machine
draw_arrow(ax, 5.6, 10.5, 4.5, 9.7, COLORS['supabase'])
# Actions → State Machine
draw_arrow(ax, 9.3, 10.5, 5.5, 9.7, COLORS['actions'])
# State Machine → Trigger Detector
draw_arrow(ax, 7.0, 8.75, 8.2, 8.75, COLORS['python'])
# Knowledge Base → RAG Indexer
draw_arrow(ax, 16.5, 10.5, 16.5, 9.7, COLORS['rag'])
# Trigger Detector → AI Agent
draw_arrow(ax, 9.5, 7.8, 3.5, 7.0, COLORS['python'])
# RAG Indexer → RAG Retriever
draw_arrow(ax, 16.0, 7.8, 8.0, 7.0, COLORS['rag'])
# AI Agent → RAG Retriever
draw_arrow(ax, 5.3, 6.0, 6.2, 6.0, COLORS['python'])
# RAG Retriever → LLaMA
draw_arrow(ax, 10.0, 6.0, 11.0, 6.0, COLORS['rag'])
# LLaMA → Agent Decisions
draw_arrow(ax, 14.8, 6.0, 15.8, 6.0, COLORS['llm'])
# AI Agent → n8n
draw_arrow(ax, 3.3, 5.0, 3.3, 4.2, COLORS['python'])
# n8n → Email
draw_arrow(ax, 5.0, 3.2, 6.2, 3.2, COLORS['n8n'])
# n8n → Push
draw_arrow(ax, 5.0, 3.0, 10.5, 3.0, COLORS['n8n'])
# n8n → In-App
draw_arrow(ax, 5.0, 2.8, 14.8, 2.8, COLORS['n8n'])
# Delivery → Outcomes
draw_arrow(ax, 7.8, 2.2, 7.0, 1.7, COLORS['delivery'])
draw_arrow(ax, 12.1, 2.2, 9.5, 1.7, COLORS['delivery'])
# Outcomes → Self-Improving
draw_arrow(ax, 9.5, 0.95, 10.5, 0.95, COLORS['posthog'])
# Self-Improving → RAG
draw_arrow(ax, 13.0, 1.5, 16.5, 7.8, COLORS['rag'])

# ── Legend ────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color=COLORS['posthog'],  label='Event Tracking (PostHog)'),
    mpatches.Patch(color=COLORS['supabase'], label='Database (Supabase)'),
    mpatches.Patch(color=COLORS['python'],   label='Python / State Machine'),
    mpatches.Patch(color=COLORS['rag'],      label='RAG Pipeline (pgvector)'),
    mpatches.Patch(color=COLORS['llm'],      label='LLM (LLaMA 3.3 70B / Groq)'),
    mpatches.Patch(color=COLORS['n8n'],      label='Automation (n8n)'),
    mpatches.Patch(color=COLORS['delivery'], label='Delivery Channels'),
    mpatches.Patch(color=COLORS['actions'],  label='GitHub Actions'),
]

ax.legend(
    handles=legend_items,
    loc='lower center',
    bbox_to_anchor=(0.5, -0.02),
    ncol=8,
    fontsize=7.5,
    framealpha=0.2,
    facecolor=COLORS['bg_card'],
    edgecolor=COLORS['border'],
    labelcolor=COLORS['text']
)

plt.tight_layout()
plt.savefig('architecture.png', dpi=150, bbox_inches='tight',
            facecolor='#0F172A', edgecolor='none')
print('✅ Architecture diagram saved as architecture.png')