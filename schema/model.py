from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    PositiveFloat,
    StringConstraints,
)

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
PathNoBackslash = Annotated[str, StringConstraints(pattern=r"^[^\\]+$")]
Glob = NonEmptyStr
UnsignedInt = Annotated[int, Field(strict=True, ge=0)]
GitUrl = Annotated[str, StringConstraints(pattern=r"((git|ssh|http(s)?)|(git@[\w\.]+))(:(\/\/)?)([\w\.@:\/\\-~]+)")]


class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"


###################
# Project section #
###################
class ChannelInlineTable(StrictBaseModel):
    channel: NonEmptyStr | AnyHttpUrl = Field(
        description="The channel the packages needs to be fetched from"
    )
    priority: int | None = Field(None, description="The priority of the channel")


Channel = NonEmptyStr | ChannelInlineTable


class Project(StrictBaseModel):
    name: NonEmptyStr = Field(
        description="The name of the project, we advice to use the name of the repository"
    )
    version: NonEmptyStr | None = Field(
        None, description="The version of the project, we advice to use semver", examples=["1.2.3"]
    )
    description: NonEmptyStr | None = Field(None, description="A short description of the project")
    authors: list[NonEmptyStr] | None = Field(
        None, description="The authors of the project", examples=["John Doe <j.doe@prefix.dev>"]
    )
    channels: list[Channel] = Field(
        None, description="The conda channels that can be used in the project"
    )
    platforms: list[NonEmptyStr] = Field(description="The platforms that the project supports")
    license: NonEmptyStr | None = Field(None, description="The license of the project")
    license_file: PathNoBackslash | None = Field(
        None, description="The path to the license file of the project"
    )
    readme: PathNoBackslash | None = Field(
        None, description="The path to the readme file of the project"
    )
    homepage: AnyHttpUrl | None = Field(None, description="The url of the homepage of the project")
    repository: AnyHttpUrl | None = Field(
        None, description="The url of the repository of the project"
    )
    documentation: AnyHttpUrl | None = Field(
        None, description="The url of the documentation of the project"
    )


########################
# Dependencies section #
########################


class MatchspecTable(StrictBaseModel):
    version: NonEmptyStr | None = Field(
        None,
        description="The version of the package in [MatchSpec](https://github.com/conda/conda/blob/078e7ee79381060217e1ec7f9b0e9cf80ecc8f3f/conda/models/match_spec.py) format",
    )
    build: NonEmptyStr | None = Field(None, description="The build string of the package")
    channel: NonEmptyStr | None = Field(
        None,
        description="The channel the packages needs to be fetched from",
        examples=["conda-forge", "pytorch", "https://repo.prefix.dev/conda-forge"],
    )


MatchSpec = NonEmptyStr | MatchspecTable
CondaPackageName = NonEmptyStr


# { version = "sdfds" extras = ["sdf"] }
# { git = "sfds", rev = "fssd" }
# { path = "asfdsf" }
# { url = "asdfs" }

class PyPIVersionRequirement(StrictBaseModel):
    version: NonEmptyStr = Field(
        None,
        description="The version of the package in [PEP 440](https://www.python.org/dev/peps/pep-0440/) format",
    )

class GitTag(StrictBaseModel):
    tag: NonEmptyStr = Field(None, description="A git tag to use")

class GitRev(StrictBaseModel):
    rev: NonEmptyStr = Field(None, description="A git sha revision to sue")

class GitBranch(StrictBaseModel):
    branch: NonEmptyStr = Field(None, description="A git branch to use")

class PyPIGitRequirement(StrictBaseModel):
    git: NonEmptyStr = Field(
        None,
        description="The git url to the repo e.g https://github.com/prefix-dev/pixi",
    )
    rev_tag_branch: GitTag | GitRev | GitBranch

class PyPIPathRequirement(StrictBaseModel):
    path: NonEmptyStr = Field(
        None,
        description="A path to a local source or wheel",
    )

class PyPIUrlRequirement(StrictBaseModel):
    url: NonEmptyStr = Field(
        None,
        description="A url to a remote source or wheel",
    )

class PyPIVersion(StrictBaseModel):
    version: NonEmptyStr = Field(
        None,
        description="The version of the package in [PEP 440](https://www.python.org/dev/peps/pep-0440/) format",
    )

class PyPIRequirementTable(StrictBaseModel):
    requirement: PyPIVersion | PyPIGitRequirement | PyPIPathRequirement | PyPIUrlRequirement
    extras: list[NonEmptyStr] | None = Field(None, description="The extras of the package")


PyPIRequirement = NonEmptyStr | PyPIRequirementTable
PyPIPackageName = NonEmptyStr

DependenciesField = Field(
    None,
    description="The conda dependencies, consisting of a package name and a requirement in [MatchSpec](https://github.com/conda/conda/blob/078e7ee79381060217e1ec7f9b0e9cf80ecc8f3f/conda/models/match_spec.py) format",
)
HostDependenciesField = Field(
    None,
    alias="host-dependencies",
    description="The host conda dependencies, used in the build process",
)
BuildDependenciesField = Field(
    None,
    alias="build-dependencies",
    description="The build conda dependencies, used in the build process",
)
Dependencies = dict[CondaPackageName, MatchSpec] | None

################
# Task section #
################
TaskName = NonEmptyStr


class TaskInlineTable(StrictBaseModel):
    cmd: list[NonEmptyStr] | NonEmptyStr | None = Field(
        None, description="The command to run the task"
    )
    cwd: PathNoBackslash | None = Field(None, description="The working directory to run the task")
    depends_on: list[NonEmptyStr] | NonEmptyStr | None = Field(
        None, description="The tasks that this task depends on"
    )
    inputs: list[Glob] | None = Field(None, description="A list of glob patterns that should be watched for changes before this command is run")
    outputs: list[Glob] | None = Field(None, description="A list of glob patterns that are generated by this command")

#######################
# System requirements #
#######################
class LibcFamily(StrictBaseModel):
    family: NonEmptyStr | None = Field(
        None, description="The family of the libc", examples=["glibc", "musl"]
    )
    version: float | NonEmptyStr | None = Field(None, description="The version of libc")


class SystemRequirements(StrictBaseModel):
    linux: PositiveFloat | NonEmptyStr | None = Field(
        None, description="The minimum version of the linux kernel"
    )
    unix: bool | NonEmptyStr | None = Field(
        None, description="Whether the project supports unix", examples=["true"]
    )
    libc: LibcFamily | float | NonEmptyStr | None = Field(
        None, description="The minimum version of glibc"
    )
    cuda: float | NonEmptyStr | None = Field(None, description="The minimum version of cuda")
    archspec: NonEmptyStr | None = Field(None, description="The architecture the project supports")
    macos: PositiveFloat | NonEmptyStr | None = Field(
        None, description="The minimum version of macos"
    )


#######################
# Environment section #
#######################
EnvironmentName = NonEmptyStr
FeatureName = NonEmptyStr
SolveGroupName = NonEmptyStr


class Environment(StrictBaseModel):
    features: list[FeatureName] | None = Field(
        None, description="The features that define the environment"
    )
    solve_group: SolveGroupName | None = Field(
        None,
        alias="solve-group",
        description="The group name for environments that should be solved together",
    )


######################
# Activation section #
######################
class Activation(StrictBaseModel):
    scripts: list[NonEmptyStr] | None = Field(
        None,
        description="The scripts to run when the environment is activated",
        examples=["activate.sh", "activate.bat"],
    )


##################
# Target section #
##################
TargetName = NonEmptyStr


class Target(StrictBaseModel):
    dependencies: Dependencies = DependenciesField
    host_dependencies: Dependencies = HostDependenciesField
    build_dependencies: Dependencies = BuildDependenciesField
    pypi_dependencies: dict[PyPIPackageName, PyPIRequirement] | None = Field(
        None, alias="pypi-dependencies", description="The pypi dependencies"
    )
    tasks: dict[TaskName, TaskInlineTable | NonEmptyStr] | None = Field(
        None, description="The tasks of the project"
    )
    activation: Activation | None = Field(
        None, description="The scripts used on the activation of the project"
    )


###################
# Feature section #
###################
class Feature(StrictBaseModel):
    channels: list[Channel] | None = Field(
        None, description="The conda channels that can be used in the feature"
    )
    platforms: list[NonEmptyStr] | None = Field(
        None,
        description="The platforms that the feature supports, union of all features combined in one environment is used for the environment.",
    )
    dependencies: Dependencies = DependenciesField
    host_dependencies: Dependencies = HostDependenciesField
    build_dependencies: Dependencies = BuildDependenciesField
    pypi_dependencies: dict[PyPIPackageName, PyPIRequirement] | None = Field(
        None, alias="pypi-dependencies", description="The pypi dependencies"
    )
    tasks: dict[TaskName, TaskInlineTable | NonEmptyStr] | None = Field(
        None, description="The tasks of the project"
    )
    activation: Activation | None = Field(
        None, description="The scripts used on the activation of the project"
    )
    system_requirements: SystemRequirements | None = Field(
        None, alias="system-requirements", description="The system requirements of the project"
    )
    target: dict[TargetName, Target] | None = Field(
        None,
        description="The targets of the project",
        examples=[{"linux": {"dependencies": {"python": "3.8"}}}],
    )


#######################
# The Manifest itself #
#######################

SchemaVersion = Annotated[int, Field(ge=1, le=1)]


class BaseManifest(StrictBaseModel):
    project: Project = Field(..., description="The projects metadata information")
    dependencies: Dependencies = DependenciesField
    host_dependencies: Dependencies = HostDependenciesField
    build_dependencies: Dependencies = BuildDependenciesField
    pypi_dependencies: dict[PyPIPackageName, PyPIRequirement] | None = Field(
        None, alias="pypi-dependencies", description="The pypi dependencies"
    )
    tasks: dict[TaskName, TaskInlineTable | NonEmptyStr] | None = Field(
        None, description="The tasks of the project"
    )
    system_requirements: SystemRequirements | None = Field(
        None, alias="system-requirements", description="The system requirements of the project"
    )
    environments: dict[EnvironmentName, Environment | list[FeatureName]] | None = Field(
        None, description="The environments of the project"
    )
    feature: dict[FeatureName, Feature] | None = Field(
        None, description="The features of the project"
    )
    activation: Activation | None = Field(
        None, description="The scripts used on the activation of the project"
    )
    target: dict[TargetName, Target] | None = Field(
        None,
        description="The targets of the project",
        examples=[{"linux": {"dependencies": {"python": "3.8"}}}],
    )
    tool: Any = Field(
        None, description="A third-party tool configuration, ignored by pixi"
    )


if __name__ == "__main__":
    print(json.dumps(BaseManifest.model_json_schema(), indent=2))
