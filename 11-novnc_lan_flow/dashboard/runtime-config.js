// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.

window.URI_RUN_NOVNC_CONFIG = {
  dashboardPort: "8192",
  visiblePcs: ["pc1", "pc2"],
  pcs: {
    pc1: { novncPort: "7901", apiPort: "9001" },
    pc2: { novncPort: "7902", apiPort: "9002" },
    pc3: { novncPort: "7903", apiPort: "9003" },
    pc4: { novncPort: "7904", apiPort: "9004" }
  }
};
