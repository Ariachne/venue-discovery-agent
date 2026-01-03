"""
Venue Discovery Web App
Complete web interface for musicians
"""

from flask import Flask, render_template_string, request, jsonify
import anthropic
import os
import re

app = Flask(__name__)

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
        
        window.onload = function() {
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
    
            // Create AbortController with 3 minute timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minutes
    
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
                    showMessage('Error: ' + data.error, 'error');
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
            container.innerHTML = venues.map((venue, idx) => `
                <div class="venue-card" onclick="researchVenue(${idx})">
                    <div class="venue-name">${venue.name}</div>
                    <div class="venue-details">
                        📍 ${venue.city}, ${venue.state}
                        ${venue.capacity ? `• 👥 Capacity: ${venue.capacity}` : ''}
                    </div>
                    <div class="venue-details">${venue.reason}</div>
                    <span class="match-score">${venue.match_score}% Match</span>
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

            // Create AbortController with 3 minute timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minutes
    
            try {
                const response = await fetch('/research', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({venue, profile})
                });

                clearTimeout(timeoutId);
                
                const data = await response.json();
                
                if (data.error) {
                    showMessage('Error: ' + data.error, 'error');
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

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=6000,
        tools=[{
           "type": "web_search_20250305",
           "name": "web_search"
        }],
        messages=[{"role": "user", "content": prompt}]
    )
    
    return parse_venues(response.content)


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

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
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


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/discover', methods=['POST'])
def discover():
    """Discover venues endpoint"""
    try:
        data = request.json
        profile = data['profile']
        target_city = data['targetCity']
        
        venues = discover_venues_api(profile, target_city)
        
        return jsonify({'venues': venues})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/research', methods=['POST'])
def research():
    """Research venue endpoint"""
    try:
        data = request.json
        venue = data['venue']
        profile = data['profile']
        
        research_text = research_venue_api(venue, profile)
        
        return jsonify({'research': research_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
