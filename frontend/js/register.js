document.getElementById('registerForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const msg = document.getElementById('msg');
  msg.className = 'msg';
  msg.textContent = '';

  const email     = document.getElementById('email').value.trim();
  const user_name = document.getElementById('user_name').value.trim();
  const password  = document.getElementById('password').value.trim();

  try {
    const res  = await fetch(`${API_BASE}/register`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, user_name, password })
    });
    const data = await res.json();

    if (res.status === 201) {
      msg.className   = 'msg success';
      msg.textContent = 'Registration successful! Redirecting to login...';
      setTimeout(() => window.location.href = 'login.html', 1500);
    } else if (res.status === 409) {
      msg.className   = 'msg error';
      msg.textContent = 'The email already exists.';
    } else {
      msg.className   = 'msg error';
      msg.textContent = data.message || 'Registration failed. Please try again.';
    }
  } catch (err) {
    msg.className   = 'msg error';
    msg.textContent = 'Network error. Please try again.';
  }
});
