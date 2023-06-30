use crate::common::package_database::{Package, PackageDatabase};
use crate::common::{LockFileExt, PixiControl};
use tempfile::TempDir;

mod common;

#[tokio::test]
pub async fn update_command() {
    let mut package_database = PackageDatabase::default();

    // Add a package `foo` that depends on `bar` both set to version 1.
    package_database.add_package(Package::build("bar", "1").finish());
    package_database.add_package(Package::build("bar", "2").finish());

    // Write the repodata to disk
    let channel_dir = TempDir::new().unwrap();
    package_database
        .write_repodata(channel_dir.path())
        .await
        .unwrap();

    let pixi = PixiControl::new().unwrap();
    pixi.init()
        .with_local_channel(channel_dir.path())
        .await
        .unwrap();
    pixi.add("bar==1").await.unwrap();

    assert!(pixi.lock_file().await.unwrap().contains_matchspec("bar==1"));

    pixi.update("bar==2");

    assert!(pixi.lock_file().await.unwrap().contains_matchspec("bar==2"));
}
