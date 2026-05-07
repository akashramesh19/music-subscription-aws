// ── Auth guard ────────────────────────────────────────────────────────────────
const email    = sessionStorage.getItem('user_email');
const userName = sessionStorage.getItem('user_name');

if (!email) {
  window.location.href = 'login.html';
}

document.getElementById('navUser').textContent = userName || email;

// ── Logout ────────────────────────────────────────────────────────────────────
document.getElementById('logoutBtn').addEventListener('click', () => {
  sessionStorage.clear();
  window.location.href = 'login.html';
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function showMsg(id, text, type) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className   = `msg-banner ${type}`;
  setTimeout(() => { el.className = 'msg-banner'; el.textContent = ''; }, 3000);
}

function imgSrc(url) {
  return url || 'https://placehold.co/220x130?text=No+Image';
}

// ── Subscriptions ─────────────────────────────────────────────────────────────
async function loadSubscriptions() {
  const list = document.getElementById('subList');
  try {
    const res  = await fetch(`${API_BASE}/subscriptions?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    const subs = data.subscriptions || [];

    if (subs.length === 0) {
      list.innerHTML = '<p class="empty-msg">You have no subscriptions yet.</p>';
      return;
    }

    list.innerHTML = subs.map(s => `
      <div class="sub-card">
        <img src="${imgSrc(s.image_url)}" alt="${s.title}" onerror="this.src='https://placehold.co/60x60?text=?'"/>
        <div class="sub-info">
          <div class="song-title">${s.title}</div>
          <div class="song-meta">${s.artist} · ${s.album} · ${s.year}</div>
        </div>
        <button class="btn-remove"
          data-title="${s.title}"
          data-album="${s.album}">
          Remove
        </button>
      </div>
    `).join('');

    // Attach remove listeners
    list.querySelectorAll('.btn-remove').forEach(btn => {
      btn.addEventListener('click', () => unsubscribe(btn.dataset.title, btn.dataset.album));
    });

  } catch (err) {
    list.innerHTML = '<p class="empty-msg">Failed to load subscriptions.</p>';
  }
}

async function unsubscribe(title, album) {
  try {
    const res = await fetch(`${API_BASE}/unsubscribe`, {
      method:  'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, title, album })
    });
    if (res.ok) {
      showMsg('subMsg', 'Unsubscribed successfully!', 'success');
      loadSubscriptions();
    } else {
      showMsg('subMsg', 'Failed to unsubscribe.', 'error');
    }
  } catch {
    showMsg('subMsg', 'Network error.', 'error');
  }
}

// ── Search ────────────────────────────────────────────────────────────────────
document.getElementById('searchBtn').addEventListener('click', searchSongs);

async function searchSongs() {
  const artist = document.getElementById('srArtist').value.trim();
  const title  = document.getElementById('srTitle').value.trim();
  const year   = document.getElementById('srYear').value.trim();
  const album  = document.getElementById('srAlbum').value.trim();

  const grid = document.getElementById('songResults');

  // At least one field must be completed
  if (!artist && !title && !year && !album) {
    grid.innerHTML = '<p class="empty-msg">Please enter at least one search field.</p>';
    return;
  }

  const params = new URLSearchParams();
  if (artist) params.append('artist', artist);
  if (title)  params.append('title',  title);
  if (year)   params.append('year',   year);
  if (album)  params.append('album',  album);

  grid.innerHTML = '<p class="empty-msg">Searching...</p>';

  try {
    const res  = await fetch(`${API_BASE}/music?${params.toString()}`);
    const data = await res.json();
    const songs = data.songs || [];

    if (songs.length === 0) {
      grid.innerHTML = '<p class="empty-msg">No result is retrieved. Please query again</p>';
      return;
    }

    grid.innerHTML = songs.map(s => `
      <div class="song-card">
        <img src="${imgSrc(s.image_url)}" alt="${s.title}" onerror="this.src='https://placehold.co/220x130?text=?'"/>
        <div class="song-title">${s.title}</div>
        <div class="song-meta">${s.artist}</div>
        <div class="song-meta">${s.album} · ${s.year}</div>
        <button class="btn-subscribe"
          data-title="${s.title}"
          data-album="${s.album}"
          data-artist="${s.artist}"
          data-year="${s.year}"
          data-image="${s.image_url || ''}">
          + Subscribe
        </button>
      </div>
    `).join('');

    grid.querySelectorAll('.btn-subscribe').forEach(btn => {
      btn.addEventListener('click', () => subscribe(btn));
    });

  } catch (err) {
    grid.innerHTML = '<p class="empty-msg">Failed to fetch songs.</p>';
  }
}

async function subscribe(btn) {
  btn.disabled = true;
  btn.textContent = 'Subscribing...';

  try {
    const res = await fetch(`${API_BASE}/subscribe`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        email,
        title:     btn.dataset.title,
        album:     btn.dataset.album,
        artist:    btn.dataset.artist,
        year:      btn.dataset.year,
        image_url: btn.dataset.image
      })
    });

    if (res.status === 201) {
      btn.textContent = '✓ Subscribed';
      showMsg('subMsg', `Subscribed to "${btn.dataset.title}"!`, 'success');
      loadSubscriptions();
    } else {
      btn.disabled = false;
      btn.textContent = '+ Subscribe';
      showMsg('subMsg', 'Failed to subscribe.', 'error');
    }
  } catch {
    btn.disabled = false;
    btn.textContent = '+ Subscribe';
    showMsg('subMsg', 'Network error.', 'error');
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadSubscriptions();
