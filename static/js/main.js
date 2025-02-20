// main.js loaded
console.log("main.js loaded");

// Mapping for the 5 discrete slider positions.
// Each slider value corresponds to a label and a bias range.
const biasMapping = {
  0: { label: "Strongly Left", range: { min: -10, max: -6 } },
  1: { label: "Lean Left", range: { min: -5, max: -2 } },
  2: { label: "Centrist / Minimal partisan", range: { min: -1, max: 1 } },
  3: { label: "Lean Right", range: { min: 2, max: 5 } },
  4: { label: "Strongly Right", range: { min: 6, max: 10 } }
};

function getPoliticalClassification(index) {
  return biasMapping[index].label;
}

function getBiasRange(index) {
  return biasMapping[index].range;
}

// Global variable to track selected topic.
let selectedTopic = null;

// Fetch headlines using the slider's discrete bias range and optional topic.
function fetchHeadlines(index, topic = null) {
  const headlinesDiv = document.getElementById('headlines');
  const { min, max } = getBiasRange(index);
  let url = `/headlines?min_bias=${min}&max_bias=${max}`;
  
  if (topic) {
    url += `&topic=${encodeURIComponent(topic)}`;
  }
  
  fetch(url)
    .then(response => response.json())
    .then(data => {
      headlinesDiv.innerHTML = ''; // Clear previous headlines
      data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'headline-card';
        card.innerHTML = `
          <div class="card-title">${item.title}</div>
          <div class="card-subtitle">${item.source_name} (Bias: ${item.bias_score})</div>
          <a href="${item.url}" target="_blank">Read more</a>
          <div class="card-date">${item.display_date}</div>
        `;
        headlinesDiv.appendChild(card);
      });
    })
    .catch(error => {
      console.error("Error fetching headlines:", error);
    });
}

// Fetch topics and create the horizontal scrollable topic button bar.
function fetchTopics() {
  const topicContainer = document.getElementById('topic-buttons');
  fetch('/topics')
    .then(response => response.json())
    .then(topics => {
      topicContainer.innerHTML = ''; // Clear existing buttons
      
      // Create Reset Filter button.
      const resetButton = document.createElement('button');
      resetButton.textContent = 'Reset Filter';
      resetButton.className = 'topic-button reset-button';
      resetButton.addEventListener('click', () => {
        selectedTopic = null;
        // Remove selected visual cue from all buttons.
        document.querySelectorAll('.topic-button').forEach(btn => btn.classList.remove('selected'));
        const slider = document.getElementById('biasSlider');
        fetchHeadlines(parseInt(slider.value));
      });
      topicContainer.appendChild(resetButton);
      
      topics.forEach(topic => {
        const button = document.createElement('button');
        button.textContent = topic;
        button.className = 'topic-button';
        
        button.addEventListener('click', () => {
          // Remove 'selected' from all topic buttons, then mark this one.
          document.querySelectorAll('.topic-button').forEach(btn => btn.classList.remove('selected'));
          button.classList.add('selected');
          
          selectedTopic = topic;
          const slider = document.getElementById('biasSlider');
          fetchHeadlines(parseInt(slider.value), selectedTopic);
        });
        
        topicContainer.appendChild(button);
      });
    })
    .catch(error => console.error('Error fetching topics:', error));
}

// Initialize on page load.
window.addEventListener('load', () => {
  const slider = document.getElementById('biasSlider');
  const sliderValue = document.getElementById('sliderValue');
  
  const initialIndex = parseInt(slider.value);
  sliderValue.textContent = getPoliticalClassification(initialIndex);
  fetchHeadlines(initialIndex, selectedTopic);
  fetchTopics();
  
  // Update headlines when slider moves, preserving the current topic filter.
  slider.addEventListener('input', (e) => {
    const index = parseInt(e.target.value);
    sliderValue.textContent = getPoliticalClassification(index);
    fetchHeadlines(index, selectedTopic);
  });
});
