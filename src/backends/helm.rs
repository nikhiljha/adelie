use color_eyre::eyre::{eyre, Result};
use serde::{Deserialize, Serialize};
use url::Url;

use super::Backend;

#[derive(Debug, Serialize, Deserialize)]
pub struct Helm {
    pub repo: Url,
    pub chart: String,
}

impl Helm {
    pub fn new(repo: Url, chart: String) -> Self {
        Self { repo, chart }
    }
}

impl Backend for Helm {
    async fn initialize(&self) -> Result<()> {
        if self.repo.scheme() == "oci" {
            return Err(eyre!("OCI repositories are not supported yet."));
        }
        if self.repo.scheme() != "https" {
            return Err(eyre!("Only HTTPS repositories are supported."));
        }

        Ok(())
    }

    async fn latest_version(&self) -> Result<String> {
        // Use reqwest to fetch the index.yaml file from the Helm repository
        // and parse it to get the latest version of the chart.
        let client = reqwest::Client::new();
        let index_url = self.repo.join("index.yaml")?;
        let index = client.get(index_url).send().await?.text().await?;
        let index: serde_yaml::Value = serde_yaml::from_str(&index)?;

        // Assert apiVersion = 1
        // let api_version = index["apiVersion"]
        //     .as_str()
        //     .ok_or_else(|| eyre!("apiVersion not found"))?;
        // if api_version != "v1" {
        //     return Err(eyre!("apiVersion must be v1"));
        // }

        // Get the latest version
        let chart = index["entries"][&self.chart]
            .as_sequence()
            .ok_or_else(|| eyre!("Chart not found"))?;
        let latest_version = chart
            .iter()
            .filter(|e| e["version"].as_str().map(lenient_semver::parse).unwrap().unwrap().pre.is_empty())
            // Largest version number by semver
            .max_by_key(|v| {
                lenient_semver::parse(v["version"].as_str().unwrap()).unwrap()
            })
            .ok_or_else(|| eyre!("No versions found"))?;
        let latest_version = latest_version["version"]
            .as_str()
            .ok_or_else(|| eyre!("Version not found"))?;

        Ok(latest_version.to_string())
    }
}
