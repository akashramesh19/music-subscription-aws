document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const msg = document.getElementById('msg');
  msg.className = 'msg';
  msg.textContent = '';

  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value.trim();

  try {
    const res  = await fetch(`${API_BASE}/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (res.ok) {
      // Store user info for main page
      sessionStorage.setItem('user_email',    data.email);
      sessionStorage.setItem('user_name',     data.user_name);
      window.location.href = 'main.html';
    } else {
      msg.className   = 'msg error';
      msg.textContent = 'email or password is invalid';
    }
  } catch (err) {
    msg.className   = 'msg error';
    msg.textContent = 'Network error. Please try again.';
  }
});
