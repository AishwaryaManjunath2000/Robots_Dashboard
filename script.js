Papa.parse("robots.csv", {
    download: true,
    skipEmptyLines: true,
    complete: function(results) {
      // Skip the first descriptive header row
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
            <p><strong>Set Available:</strong> ${robot["Set Available"]} (${robot["Set size"]})</p>
            <a href="${robot["Purchase Website"]}" target="_blank">More Info</a>
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
  