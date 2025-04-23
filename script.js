Papa.parse("robots.csv", {
    download: true,
    header: true,
    complete: function(results) {
      const data = results.data;
      const container = document.getElementById("dashboard");
      const searchInput = document.getElementById("search");
  
      function displayData(filteredData) {
        container.innerHTML = ""; // Clear previous results
  
        filteredData.forEach(robot => {
          const div = document.createElement("div");
          div.classList.add("robot-card");
  
          div.innerHTML = `
            <h2>${robot.Name}</h2>
            <p><strong>Manufacturer:</strong> ${robot.Manufacturer}</p>
            <p><strong>Price:</strong> ${robot.Price}</p>
            <p><strong>Set Available:</strong> ${robot["Set Available"]} (${robot["Set size"]})</p>
            <a href="${robot["Purchase Website"]}" target="_blank">More Info</a>
          `;
          container.appendChild(div);
        });
      }
  
      // Display all data by default
      displayData(data);
  
      // Search filter
      searchInput.addEventListener("input", function () {
        const query = searchInput.value.toLowerCase();
        const filtered = data.filter(robot =>
          robot.Name.toLowerCase().includes(query) ||
          robot.Manufacturer.toLowerCase().includes(query)
        );
        displayData(filtered);
      });
    }
  });
  