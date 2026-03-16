"""
Venue Discovery Web App
Complete web interface for musicians
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import timedelta
import anthropic
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')
app.permanent_session_lifetime = timedelta(days=7)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Venue Discovery Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        .login-card h1 { color: #667eea; margin-bottom: 8px; font-size: 24px; }
        .login-card p { color: #6b7280; margin-bottom: 24px; }
        .login-card input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 16px;
        }
        .login-card input:focus { outline: none; border-color: #667eea; }
        .login-card button {
            width: 100%;
            padding: 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        .login-card button:hover { background: #5568d3; }
        .error-msg { color: #991b1b; background: #fee2e2; padding: 10px; border-radius: 8px; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>Venue Discovery Agent</h1>
        <p>Enter password to continue</p>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Password" autofocus required>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>
"""


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        password = os.environ.get('PASSWORD')
        if not password:
            return f(*args, **kwargs)

        # Check query parameter (for API calls)
        if request.args.get('password') == password:
            return f(*args, **kwargs)

        # Check session cookie
        if session.get('authenticated'):
            return f(*args, **kwargs)

        # Not authenticated
        wants_json = request.is_json or request.content_type == 'application/json'
        if wants_json:
            return jsonify({'error': 'Authentication required'}), 401
        return render_template_string(LOGIN_TEMPLATE, error=None), 401

    return decorated

# HTML Template - Single page application
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Venue Discovery Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: #667eea;
            color: white;
            padding: 14px 28px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            width: 100%;
        }
        
        .btn:hover {
            background: #5568d3;
        }
        
        .btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }
        
        .venue-card {
            border: 2px solid #e5e7eb;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: border-color 0.3s;
            cursor: pointer;
        }
        
        .venue-card:hover {
            border-color: #667eea;
        }
        
        .venue-name {
            font-size: 20px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 8px;
        }
        
        .venue-details {
            color: #6b7280;
            margin-bottom: 8px;
        }
        
        .match-score {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }

        .btn-save {
            background: #10b981;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 10px;
            display: inline-block;
        }

        .btn-save:hover {
            background: #059669;
        }

        .btn-save:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .btn-save-all {
            background: #10b981;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-bottom: 20px;
        }

        .btn-save-all:hover {
            background: #059669;
        }

        .btn-save-all:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        details summary {
            cursor: pointer;
            color: #667eea;
            font-weight: 600;
            padding: 5px 0;
        }

        details summary:hover {
            opacity: 0.8;
        }

        .settings-inner {
            margin-top: 15px;
        }

        .saved-badge {
            display: inline-block;
            background: #d1fae5;
            color: #065f46;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 8px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f4f6;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .research-section {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        
        .hidden {
            display: none;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .error {
            background: #fee2e2;
            border: 2px solid #fecaca;
            color: #991b1b;
        }
        
        .success {
            background: #d1fae5;
            border: 2px solid #a7f3d0;
            color: #065f46;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Venue Discovery Agent</h1>
            <p>Find and research perfect venues for your tour</p>
        </div>
        
        <div class="card">
            <h2>Your Artist Profile</h2>
            <form id="profileForm">
                <div class="form-group">
                    <label>Artist/Band Name *</label>
                    <input type="text" id="artistName" required>
                </div>
                <div class="form-group">
                    <label>Genre *</label>
                    <input type="text" id="genre" placeholder="e.g., Jazz, Rock, Folk" required>
                </div>
                <div class="form-group">
                    <label>Typical Draw Size *</label>
                    <input type="text" id="drawSize" placeholder="e.g., 200-400" required>
                </div>
                <div class="form-group">
                    <label>Fee Range</label>
                    <input type="text" id="feeRange" placeholder="e.g., $1,500-3,000">
                </div>
                <div class="form-group">
                    <label>Home Base</label>
                    <input type="text" id="homeBase" placeholder="e.g., Nashville, TN">
                </div>
                <div class="form-group">
                    <label>Similar Artists</label>
                    <input type="text" id="similarArtists" placeholder="e.g., Artist A, Artist B">
                </div>
            </form>
        </div>
        
        <div class="card">
            <h2>Discover Venues</h2>
            <div class="form-group">
                <label>Target City *</label>
                <input type="text" id="targetCity" placeholder="e.g., New York, NY" required>
            </div>
            <button class="btn" onclick="discoverVenues()" id="discoverBtn">
                🔍 Discover Venues
            </button>
        </div>

        <div class="card" style="background: #f8f9ff;">
            <details id="platformDetails">
                <summary>Booking Platform Settings</summary>
                <div class="settings-inner">
                    <p style="color: #6b7280; margin-bottom: 15px; font-size: 14px;">
                        Connect to your gig booking platform to save discovered venues directly into your outreach pipeline.
                    </p>
                    <div class="form-group">
                        <label>Platform URL</label>
                        <input type="url" id="platformUrl" placeholder="e.g., https://your-app.up.railway.app">
                    </div>
                    <div class="form-group">
                        <label>Musician ID</label>
                        <input type="text" id="musicianId" placeholder="Your musician ID from the platform">
                    </div>
                    <button class="btn" onclick="savePlatformSettings()" style="background: #667eea;">
                        Save Settings
                    </button>
                </div>
            </details>
        </div>
        
        <div id="message" class="hidden"></div>
        
        <div id="loadingDiscover" class="card loading hidden">
            <div class="spinner"></div>
            <h3>Discovering venues...</h3>
            <p>This may take 30-60 seconds</p>
        </div>
        
        <div id="venuesSection" class="card hidden">
            <h2>Discovered Venues</h2>
            <div id="venuesList"></div>
        </div>
        
        <div id="loadingResearch" class="card loading hidden">
            <div class="spinner"></div>
            <h3>Researching venue...</h3>
            <p>This may take 30-60 seconds</p>
        </div>
        
        <div id="researchSection" class="card hidden">
            <h2 id="researchTitle"></h2>
            <button class="btn" onclick="downloadResearch()" style="margin-bottom: 20px">
                📥 Download Report
            </button>
            <div id="researchContent" class="research-section"></div>
        </div>
    </div>
    
    <script>
        let currentVenues = [];
        let currentResearch = '';
        let currentVenueName = '';
        let platformConfig = { url: '', musicianId: '' };

        window.onload = function() {
            // Load artist profile
            const saved = localStorage.getItem('artistProfile');
            if (saved) {
                const profile = JSON.parse(saved);
                document.getElementById('artistName').value = profile.name || '';
                document.getElementById('genre').value = profile.genre || '';
                document.getElementById('drawSize').value = profile.drawSize || '';
                document.getElementById('feeRange').value = profile.feeRange || '';
                document.getElementById('homeBase').value = profile.homeBase || '';
                document.getElementById('similarArtists').value = profile.similarArtists || '';
            }

            // Load platform settings
            const platformSaved = localStorage.getItem('platformConfig');
            if (platformSaved) {
                platformConfig = JSON.parse(platformSaved);
                document.getElementById('platformUrl').value = platformConfig.url || '';
                document.getElementById('musicianId').value = platformConfig.musicianId || '';
            }
        };
        
        function saveProfile() {
            const profile = {
                name: document.getElementById('artistName').value,
                genre: document.getElementById('genre').value,
                drawSize: document.getElementById('drawSize').value,
                feeRange: document.getElementById('feeRange').value,
                homeBase: document.getElementById('homeBase').value,
                similarArtists: document.getElementById('similarArtists').value
            };
            localStorage.setItem('artistProfile', JSON.stringify(profile));
            return profile;
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            msg.classList.remove('hidden');
            setTimeout(() => msg.classList.add('hidden'), 5000);
        }
        
        async function discoverVenues() {
    const profile = saveProfile();
    const targetCity = document.getElementById('targetCity').value;

    if (!profile.name || !profile.genre || !targetCity) {
        showMessage('Please fill in at least Artist Name, Genre, and Target City', 'error');
        return;
    }

    document.getElementById('discoverBtn').disabled = true;
    document.getElementById('loadingDiscover').classList.remove('hidden');
    document.getElementById('venuesSection').classList.add('hidden');
    document.getElementById('researchSection').classList.add('hidden');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    try {
        const response = await fetch('/discover', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({profile, targetCity}),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await response.json();
        
        if (data.error) {
            console.log('Error received:', data.error); // Debug log
            
            // Check if it's a rate limit error (check multiple variations)
            const errorLower = data.error.toLowerCase();
            if (errorLower.includes('rate') || errorLower.includes('limit')) {
                showMessage('⏱️ Rate limit reached. Waiting 60 seconds and retrying...', 'error');
                
                // Show countdown
                let countdown = 60;
                const countdownInterval = setInterval(() => {
                    countdown--;
                    showMessage(`⏱️ Rate limit reached. Retrying in ${countdown} seconds...`, 'error');
                }, 1000);
                
                // Wait 60 seconds
                await new Promise(resolve => setTimeout(resolve, 60000));
                clearInterval(countdownInterval);
                
                // Retry the request
                showMessage('Retrying now...', 'success');
                document.getElementById('loadingResearch').classList.remove('hidden');
                await researchVenue(index);
                return;
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        } else {
            currentVenues = data.venues;
            displayVenues(data.venues);
            showMessage(`Found ${data.venues.length} venues!`, 'success');
        }
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            showMessage('Request timed out after 3 minutes. Please try again.', 'error');
        } else {
            showMessage('Failed to discover venues. Please try again.', 'error');
        }
        console.error('Discover error:', error);
    } finally {
        document.getElementById('discoverBtn').disabled = false;
        document.getElementById('loadingDiscover').classList.add('hidden');
    }
}
        
        function displayVenues(venues) {
            const container = document.getElementById('venuesList');

            // Add "Save All" button if platform is configured
            let saveAllBtn = '';
            if (platformConfig.url && platformConfig.musicianId) {
                saveAllBtn = `<button class="btn-save-all" onclick="saveAllVenuesToPlatform(event)">Save All ${venues.length} Venues to Platform</button>`;
            }

            container.innerHTML = saveAllBtn + venues.map((venue, idx) => `
                <div class="venue-card" onclick="researchVenue(${idx})">
                    <div class="venue-name">${venue.name} <span id="saved-badge-${idx}" class="saved-badge" style="display:none;">Saved</span></div>
                    <div class="venue-details">
                        📍 ${venue.city}, ${venue.state}
                        ${venue.capacity ? `• 👥 Capacity: ${venue.capacity}` : ''}
                    </div>
                    <div class="venue-details">${venue.reason}</div>
                    <span class="match-score">${venue.match_score}% Match</span>
                    ${platformConfig.url && platformConfig.musicianId ?
                        `<button class="btn-save" id="save-btn-${idx}" onclick="saveVenueToPlatform(event, ${idx})">Save to Platform</button>` : ''}
                </div>
            `).join('');

            document.getElementById('venuesSection').classList.remove('hidden');
        }
        
        async function researchVenue(index) {
    const venue = currentVenues[index];
    const profile = saveProfile();
    
    currentVenueName = venue.name;
    
    document.getElementById('loadingResearch').classList.remove('hidden');
    document.getElementById('researchSection').classList.add('hidden');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    try {
        const response = await fetch('/research', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({venue, profile}),
            signal: controller.signal
        });

clearTimeout(timeoutId);
        const data = await response.json();
        
        if (data.error) {
            console.log('Error received:', data.error); // Debug log
            
            // Check if it's a rate limit error (check multiple variations)
            const errorLower = data.error.toLowerCase();
            if (errorLower.includes('rate') || errorLower.includes('limit')) {
                showMessage('⏱️ Rate limit reached. Waiting 60 seconds and retrying...', 'error');
                
                // Show countdown
                let countdown = 60;
                const countdownInterval = setInterval(() => {
                    countdown--;
                    showMessage(`⏱️ Rate limit reached. Retrying in ${countdown} seconds...`, 'error');
                }, 1000);
                
                // Wait 60 seconds
                await new Promise(resolve => setTimeout(resolve, 60000));
                clearInterval(countdownInterval);
                
                // Retry the request
                showMessage('Retrying now...', 'success');
                document.getElementById('loadingResearch').classList.remove('hidden');
                await researchVenue(index);
                return;
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        } else {
            currentResearch = data.research;
            document.getElementById('researchTitle').textContent = `Research: ${venue.name}`;
            document.getElementById('researchContent').textContent = data.research;
            document.getElementById('researchSection').classList.remove('hidden');
            document.getElementById('researchSection').scrollIntoView({behavior: 'smooth'});
        }
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            showMessage('Request timed out after 3 minutes. Please try again.', 'error');
        } else {
            showMessage('Failed to research venue. Please try again.', 'error');
        }
        console.error('Research error:', error);
    } finally {
        document.getElementById('loadingResearch').classList.add('hidden');
    }
}
        
        function savePlatformSettings() {
            platformConfig.url = document.getElementById('platformUrl').value.replace(/\/+$/, '');
            platformConfig.musicianId = document.getElementById('musicianId').value.trim();

            if (!platformConfig.url || !platformConfig.musicianId) {
                showMessage('Please fill in both Platform URL and Musician ID', 'error');
                return;
            }

            localStorage.setItem('platformConfig', JSON.stringify(platformConfig));
            showMessage('Platform settings saved! Save buttons will appear on discovered venues.', 'success');

            // Re-render venues if we have any, to show save buttons
            if (currentVenues.length > 0) {
                displayVenues(currentVenues);
            }
        }

        function normalizeUrl(url) {
            if (!url || url.toLowerCase() === 'unknown') return undefined;
            if (url.startsWith('http://') || url.startsWith('https://')) return url;
            return 'https://' + url;
        }

        function transformVenueForPlatform(venue) {
            const profile = saveProfile();
            const v = {
                musicianId: platformConfig.musicianId,
                name: venue.name,
                city: venue.city,
                state: venue.state || 'Unknown',
                country: 'USA',
                venueType: venue.type || 'other',
                website: normalizeUrl(venue.website)
            };
            if (venue.capacity) v.capacity = venue.capacity;
            return v;
        }

        async function saveVenueToPlatform(event, index) {
            event.stopPropagation(); // Don't trigger research click

            if (!platformConfig.url || !platformConfig.musicianId) {
                showMessage('Please configure Platform Settings first', 'error');
                document.getElementById('platformDetails').open = true;
                return;
            }

            const btn = document.getElementById('save-btn-' + index);
            if (btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

            const venue = currentVenues[index];
            const transformed = transformVenueForPlatform(venue);

            try {
                const response = await fetch(platformConfig.url + '/api/venues/bulk', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Musician-Id': platformConfig.musicianId
                    },
                    body: JSON.stringify({ venues: [transformed] })
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.error || 'Server returned ' + response.status);
                }

                const result = await response.json();
                showMessage('Saved ' + venue.name + ' to platform!', 'success');

                // Show saved badge
                const badge = document.getElementById('saved-badge-' + index);
                if (badge) badge.style.display = 'inline-block';
                if (btn) { btn.textContent = 'Saved'; }
            } catch (error) {
                console.error('Save error:', error);
                showMessage('Failed to save: ' + error.message, 'error');
                if (btn) { btn.disabled = false; btn.textContent = 'Save to Platform'; }
            }
        }

        async function saveAllVenuesToPlatform(event) {
            event.stopPropagation();

            if (!platformConfig.url || !platformConfig.musicianId) {
                showMessage('Please configure Platform Settings first', 'error');
                document.getElementById('platformDetails').open = true;
                return;
            }

            const transformed = currentVenues.map(v => transformVenueForPlatform(v));

            try {
                const response = await fetch(platformConfig.url + '/api/venues/bulk', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Musician-Id': platformConfig.musicianId
                    },
                    body: JSON.stringify({ venues: transformed })
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.error || 'Server returned ' + response.status);
                }

                const result = await response.json();
                showMessage('Saved ' + result.created + ' venue(s) to platform!', 'success');

                // Show all badges
                currentVenues.forEach((v, i) => {
                    const badge = document.getElementById('saved-badge-' + i);
                    if (badge) badge.style.display = 'inline-block';
                    const btn = document.getElementById('save-btn-' + i);
                    if (btn) { btn.textContent = 'Saved'; btn.disabled = true; }
                });
            } catch (error) {
                console.error('Save all error:', error);
                showMessage('Failed to save venues: ' + error.message, 'error');
            }
        }

        function downloadResearch() {
            const element = document.createElement('a');
            const file = new Blob([currentResearch], {type: 'text/plain'});
            element.href = URL.createObjectURL(file);
            element.download = `${currentVenueName.replace(/[^a-z0-9]/gi, '_')}_research.txt`;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            showMessage('Report downloaded!', 'success');
        }
    </script>
</body>
</html>
"""


def get_client():
    """Get Anthropic client"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def discover_venues_api(profile, target_city):
    """Discover venues using Claude"""
    client = get_client()
    
    prompt = f"""Find 10-15 music venues in {target_city} for this artist:

Artist: {profile['name']}
Genre: {profile['genre']}
Draw: {profile['drawSize']}
Similar Artists: {profile.get('similarArtists', 'N/A')}

For EACH venue, format EXACTLY like this:
---
VENUE: [name]
CITY: [city]
STATE: [state]
CAPACITY: [number or unknown]
TYPE: [type]
WEBSITE: [url or unknown]
MATCH_SCORE: [0-100]
REASON: [one sentence]
---

Search thoroughly for venues that book {profile['genre']} music."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return parse_venues(response.content)
        
    except anthropic.RateLimitError as e:
        raise Exception("RATE_LIMIT_ERROR")
    except Exception as e:
        print(f"Discover error: {e}")
        raise


def parse_venues(content):
    """Parse venues from Claude response"""
    venues = []
    text = ""
    for block in content:
        if hasattr(block, 'text'):
            text += block.text
    
    blocks = text.split('---')
    
    for block in blocks:
        if 'VENUE:' not in block:
            continue
        
        try:
            venue = {}
            
            m = re.search(r'VENUE:\s*(.+?)(?:\n|$)', block)
            if m:
                venue['name'] = m.group(1).strip()
            
            m = re.search(r'CITY:\s*(.+?)(?:\n|$)', block)
            if m:
                venue['city'] = m.group(1).strip()
            
            m = re.search(r'STATE:\s*(.+?)(?:\n|$)', block)
            if m:
                venue['state'] = m.group(1).strip()
            
            m = re.search(r'CAPACITY:\s*(.+?)(?:\n|$)', block)
            if m:
                cap = m.group(1).strip()
                if cap.lower() != 'unknown':
                    cm = re.search(r'\d+', cap)
                    if cm:
                        venue['capacity'] = int(cm.group())
            
            m = re.search(r'TYPE:\s*(.+?)(?:\n|$)', block)
            if m:
                venue['type'] = m.group(1).strip()
            
            m = re.search(r'WEBSITE:\s*(.+?)(?:\n|$)', block)
            if m:
                website = m.group(1).strip()
                venue['website'] = None if website.lower() == 'unknown' else website
            
            m = re.search(r'MATCH_SCORE:\s*(\d+)', block)
            if m:
                venue['match_score'] = int(m.group(1))
            else:
                venue['match_score'] = 70
            
            m = re.search(r'REASON:\s*(.+?)(?:\n|---|$)', block, re.DOTALL)
            if m:
                venue['reason'] = m.group(1).strip()
            
            if 'name' in venue and 'city' in venue:
                venues.append(venue)
        except Exception as e:
            print(f"Parse error: {e}")
            continue
    
    return venues


def research_venue_api(venue, profile):
    """Research a specific venue"""
    import anthropic
    
    client = get_client()
    
    prompt = f"""Deep research on this venue for booking:

VENUE: {venue['name']}
Location: {venue['city']}, {venue['state']}
Website: {venue.get('website', 'Unknown')}

ARTIST: {profile['name']}
Genre: {profile['genre']}
Draw: {profile['drawSize']}
Fee Range: {profile.get('feeRange', 'N/A')}

Provide detailed intelligence on:

1. BOOKING CONTACT
   - Name, title, email, phone
   - Best contact method and timing

2. BOOKING PROCESS
   - Lead time, decision process, response time
   - EPK requirements

3. RECENT ACTIVITY
   - Recent shows, current booking activity
   - Similar artists played here

4. DEAL STRUCTURE  
   - Typical guarantees, percentage splits
   - Merch terms, what's included

5. STRATEGIC VALUE
   - Venue prestige, market importance
   - Career building potential

6. NEXT STEPS
   - Specific action items for outreach

Be thorough. Use web search extensively."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{"role": "user", "content": prompt}]
        )
        
        research = ""
        for block in response.content:
            if hasattr(block, 'text'):
                research += block.text
        
        return research
        
    except anthropic.RateLimitError as e:
        # Return special error that frontend can detect
        raise Exception("RATE_LIMIT_ERROR")
    except Exception as e:
        print(f"Research error: {e}")
        raise


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    password = os.environ.get('PASSWORD')
    if not password:
        return redirect('/')

    if request.method == 'POST':
        if request.form.get('password') == password:
            session.permanent = True
            session['authenticated'] = True
            return redirect('/')
        return render_template_string(LOGIN_TEMPLATE, error='Wrong password'), 401

    return render_template_string(LOGIN_TEMPLATE, error=None)


@app.route('/')
@require_auth
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/discover', methods=['POST'])
@require_auth
def discover():
    """Discover venues endpoint"""
    try:
        data = request.json
        profile = data['profile']
        target_city = data['targetCity']
        
        print(f"Discovering venues for {profile.get('name')} in {target_city}")
        venues = discover_venues_api(profile, target_city)
        
        return jsonify({'venues': venues})
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR in /discover: {error_msg}")
        
        # Return rate limit error with special format
        if 'RATE_LIMIT' in error_msg:
            return jsonify({'error': 'RATE_LIMIT_ERROR'}), 429
        else:
            return jsonify({'error': error_msg}), 500


@app.route('/research', methods=['POST'])
@require_auth
def research():
    """Research venue endpoint"""
    try:
        data = request.json
        venue = data['venue']
        profile = data['profile']
        
        print(f"Researching venue: {venue.get('name')}")
        research_text = research_venue_api(venue, profile)
        
        return jsonify({'research': research_text})
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR in /research: {error_msg}")
        
        # Return rate limit error with special format
        if 'RATE_LIMIT' in error_msg:
            return jsonify({'error': 'RATE_LIMIT_ERROR'}), 429
        else:
            return jsonify({'error': error_msg}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
