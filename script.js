Papa.parse("robots.csv", {
    download: true,
    skipEmptyLines: true,
    complete: function(results) {
      const headers = results.data[1];
      const rows = results.data.slice(2);
  
      const data = rows.map(row => {
        const robot = {};
        headers.forEach((header, i) => {
          robot[header] = row[i];
        });
        return robot;
      });
  
      const container = document.getElementById("dashboard");
      const searchInput = document.getElementById("search");
  
      function displayData(filteredData) {
        container.innerHTML = "";
  
        filteredData.forEach(robot => {
          const div = document.createElement("div");
          div.classList.add("robot-card");
  
          div.innerHTML = `
            <h2>${robot.Name}</h2>
            <p><strong>Manufacturer:</strong> ${robot.Manufacturer}</p>
            <p><strong>Price:</strong> ${robot["Price "] || "N/A"}</p>
            <p><strong>Grade:</strong> ${robot["Min Grade Level"] || "N/A"} | <strong>Age:</strong> ${robot["Min Age"] || "N/A"}</p>
  
            <details>
              <summary>🔽 Classroom & Accessibility Info</summary>
              <p><strong>Set Available:</strong> ${robot["Set Available"] || "No"} (${robot["Set size"] || "N/A"})</p>
              <p><strong>Max Users:</strong> ${robot["Max Users"] || "N/A"}</p>
              <p><strong>Classroom Set Price:</strong> ${robot["Price per Classroom Set"] || "N/A"}</p>
  
              <p><strong>Rechargeable:</strong> ${robot.Rechargeable}</p>
              <p><strong>Batteries:</strong> ${robot.Batteries}</p>
              <p><strong>Device Required:</strong> ${robot["Device Required"]}</p>
              <p><strong>Auditory Cues:</strong> ${robot["Auditory Accessibility"]}</p>
              <p><strong>Visual Cues:</strong> ${robot["Visual Accessibility"]}</p>
            </details>
  
            <details>
              <summary>🔽 Full Description</summary>
              <p>${robot.Description || "N/A"}</p>
            </details>
  
            <p>
              <a href="${robot["Purchase Website"]}" target="_blank">Purchase Link</a><br>
              <a href="${robot["Manfacturer Website"]}" target="_blank">Manufacturer Website</a>
            </p>
          `;
          container.appendChild(div);
        });
      }
  
      displayData(data);
  
      searchInput.addEventListener("input", function () {
        const query = searchInput.value.toLowerCase();
        const filtered = data.filter(robot =>
          robot.Name?.toLowerCase().includes(query) ||
          robot.Manufacturer?.toLowerCase().includes(query)
        );
        displayData(filtered);
      });
    }
  });
  