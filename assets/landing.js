// Shared JS for all Tel-Chetz landing pages.
// Handles: FAQ accordion · CTA form submission to /api/lead · lucide icons.

(function () {
  // FAQ accordion
  document.querySelectorAll('.faq-lp-q').forEach(function (q) {
    q.addEventListener('click', function () {
      var item = q.parentElement;
      var wasOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-lp-item').forEach(function (i) { i.classList.remove('open'); });
      if (!wasOpen) item.classList.add('open');
    });
  });

  // CTA form submission → /api/lead
  var form = document.querySelector('.lp-cta-form');
  if (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      var input = form.querySelector('input[name="email"]');
      var btn = form.querySelector('button');
      var status = document.getElementById('lp-cta-status');
      var email = (input.value || '').trim();
      if (!email) return;
      var prevHtml = btn.innerHTML;
      btn.disabled = true;
      input.disabled = true;
      btn.innerHTML = 'שולחים…';
      if (status) { status.textContent = ''; status.style.color = 'rgba(238,242,247,0.6)'; }
      try {
        var resp = await fetch('/api/lead', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ email: email, message: 'מעמוד: ' + location.pathname })
        });
        var data = await resp.json().catch(function () { return {}; });
        if (resp.ok && data.ok) {
          btn.innerHTML = '✓ קיבלנו — נחזור אליכם';
          btn.style.background = 'var(--success)';
          btn.style.color = '#fff';
          input.value = '';
          if (status) { status.style.color = 'rgba(16,185,129,0.85)'; status.textContent = 'הבקשה התקבלה. נחזור אליכם תוך יום עסקים.'; }
        } else {
          var reason = data.error === 'invalid_email'
            ? 'נראה שהאימייל לא תקין — בדקו את ה־@ ואת הדומיין.'
            : data.error === 'rate_limited'
            ? 'כבר קיבלנו בקשה מכם. צריך עכשיו? התקשרו 02-375-0599.'
            : 'לא הצלחנו לשלוח כרגע. התקשרו 02-375-0599 ונסגור את זה בטלפון.';
          btn.innerHTML = prevHtml; btn.disabled = false; input.disabled = false;
          if (status) { status.style.color = 'rgba(220,38,38,0.9)'; status.textContent = reason; }
          if (typeof lucide !== 'undefined') lucide.createIcons();
          return;
        }
      } catch (err) {
        btn.innerHTML = prevHtml; btn.disabled = false; input.disabled = false;
        if (status) { status.style.color = 'rgba(220,38,38,0.9)'; status.textContent = 'אין חיבור לאינטרנט. נסו שוב — או התקשרו 02-375-0599.'; }
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
      }
      setTimeout(function () {
        btn.innerHTML = prevHtml; btn.style.background = ''; btn.style.color = '';
        btn.disabled = false; input.disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();
      }, 6000);
    });
  }

  // Lucide icons (guard)
  if (typeof lucide !== 'undefined') lucide.createIcons();
})();
