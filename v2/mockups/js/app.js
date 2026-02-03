/**
 * QualCoder v2 - Interactive Mockup JavaScript
 * Common functionality for all mockup pages
 */

// ============================================
// THEME TOGGLE
// ============================================

function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('qualcoder-theme', newTheme);
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('qualcoder-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  }
});

// ============================================
// SIDEBAR TOGGLE
// ============================================

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('qualcoder-sidebar-collapsed', sidebar.classList.contains('collapsed'));
  }
}

// Load saved sidebar state on page load
document.addEventListener('DOMContentLoaded', () => {
  const isCollapsed = localStorage.getItem('qualcoder-sidebar-collapsed') === 'true';
  const sidebar = document.getElementById('sidebar');
  if (sidebar && isCollapsed) {
    sidebar.classList.add('collapsed');
  }
});

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + K for search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.focus();
    }
  }

  // Escape to close modals
  if (e.key === 'Escape') {
    const modals = document.querySelectorAll('.modal.active');
    modals.forEach(modal => {
      modal.classList.remove('active');
    });
    const backdrops = document.querySelectorAll('.modal-backdrop.active');
    backdrops.forEach(backdrop => {
      backdrop.classList.remove('active');
    });
  }
});

// ============================================
// CODE TREE INTERACTIONS
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Toggle code tree expansion
  document.querySelectorAll('.code-tree-node').forEach(node => {
    node.addEventListener('click', (e) => {
      const item = node.closest('.code-tree-item');
      if (item && item.querySelector('.code-tree-children')) {
        item.classList.toggle('expanded');
      }
    });
  });
});

// ============================================
// DROPDOWN MENUS
// ============================================

function toggleDropdown(dropdownId) {
  const dropdown = document.getElementById(dropdownId);
  if (dropdown) {
    dropdown.classList.toggle('open');
  }
}

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown.open').forEach(dropdown => {
      dropdown.classList.remove('open');
    });
  }
});

// ============================================
// TOOLTIPS
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Simple tooltip positioning (CSS-based tooltips are used by default)
  // This is for any JavaScript-enhanced tooltips if needed
});

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info', duration = 3000) {
  const container = document.querySelector('.toast-container') || createToastContainer();

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      ${getToastIcon(type)}
    </svg>
    <div class="toast-content">
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  `;

  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

function createToastContainer() {
  const container = document.createElement('div');
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

function getToastIcon(type) {
  switch (type) {
    case 'success':
      return '<polyline points="20,6 9,17 4,12"/>';
    case 'error':
      return '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>';
    case 'warning':
      return '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>';
    default:
      return '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>';
  }
}

// ============================================
// ANIMATED COUNTERS
// ============================================

function animateCounter(element, target, duration = 1000) {
  const start = 0;
  const increment = target / (duration / 16);
  let current = start;

  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 16);
}

// ============================================
// PROGRESS BAR ANIMATIONS
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Animate progress bars on scroll into view
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fill = entry.target.querySelector('.frequency-fill, .progress-bar');
        if (fill) {
          fill.style.width = fill.dataset.width || fill.style.width;
        }
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.frequency-bar, .progress').forEach(bar => {
    observer.observe(bar);
  });
});

// ============================================
// TAB NAVIGATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.analysis-tab, .right-panel-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      const parent = tab.parentElement;
      parent.querySelectorAll('.analysis-tab, .right-panel-tab').forEach(t => {
        t.classList.remove('active');
      });
      tab.classList.add('active');
    });
  });
});

// ============================================
// FILTER BUTTONS
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.filter-btn, .stat-compact').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const parent = btn.parentElement;
      parent.querySelectorAll('.filter-btn, .stat-compact').forEach(b => {
        b.classList.remove('active');
      });
      btn.classList.add('active');
    });
  });
});

// ============================================
// MOCK DATA FOR DEMOS
// ============================================

const mockCodes = [
  { id: 1, name: 'Work-life balance', color: '#8b5cf6', count: 45, category: 'Workplace Experience' },
  { id: 2, name: 'Remote challenges', color: '#14b8a6', count: 38, category: 'Workplace Experience' },
  { id: 3, name: 'Team collaboration', color: '#f59e0b', count: 32, category: 'Communication' },
  { id: 4, name: 'Meeting fatigue', color: '#ef4444', count: 26, category: 'Communication' },
  { id: 5, name: 'Technology issues', color: '#3b82f6', count: 25, category: 'Infrastructure' },
  { id: 6, name: 'Flexibility benefits', color: '#22c55e', count: 21, category: 'Workplace Experience' },
  { id: 7, name: 'Management support', color: '#ec4899', count: 19, category: 'Organizational' },
];

const mockSources = [
  { id: 1, name: 'Interview_P08.txt', type: 'text', size: '2,450 words', codes: 8, status: 'in-progress' },
  { id: 2, name: 'Interview_P07.txt', type: 'text', size: '3,120 words', codes: 12, status: 'coded' },
  { id: 3, name: 'Interview_P09.txt', type: 'text', size: '2,890 words', codes: 0, status: 'pending' },
  { id: 4, name: 'Survey_Results_Q3.pdf', type: 'pdf', size: '24 pages', codes: 5, status: 'in-progress' },
];

const mockCases = [
  { id: 1, name: 'Participant 01', sources: 2, codes: 28, age: 32, role: 'Engineer' },
  { id: 2, name: 'Participant 02', sources: 3, codes: 42, age: 38, role: 'PM' },
  { id: 3, name: 'Participant 03', sources: 1, codes: 15, age: 27, role: 'Designer' },
];

// ============================================
// UTILITY FUNCTIONS
// ============================================

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(date) {
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

// ============================================
// INITIALIZE
// ============================================

console.log('QualCoder v2 Mockup loaded');
console.log('Theme:', document.documentElement.getAttribute('data-theme'));
