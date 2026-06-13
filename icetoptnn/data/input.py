"""
    IceTop-TNN data generation input definition.
"""

from pathlib import Path;
from enum import ReprEnum;
import functools;

import yaml

from ..util import I3FILE_EXTENSIONS, get_ext, validate_ext;

class InputResourceType(str, ReprEnum):
    """
        The type of inputs that the file(s) represent.
    """

    GCD   = "GCD";
    EVENT = "EVENT"; 

class InputFiles:
    """
        A file or set of files to be used for data processing
    """

    files: list[Path];
    """A list of files or directories to include in the training process."""

    resource: InputResourceType = InputResourceType.EVENT;
    """The resource that the referenced files represent"""

    layout: str
    """
        The detector layout used by these files. For GCD files, defines the layout the GCD is for.
    """

class InputDefinition:
    """
        Input source definition with information on where to find
        dataset source files.
    """
    
    def get_files(self) -> list[InputFiles]:
        """Get all InputFiles for this definition"""
        raise NotImplementedError(); # Would be abstract but ABC is a metaclass and so is YAMLObject

class InputDefinitionWithData(InputDefinition):
    """
        Input definition with InputFile data.

        It is the inheriting class's job to add the data to the final InputFiles
    """

    resource: InputResourceType = InputResourceType.EVENT;
    layout:   str;

class GroupDefinition(InputDefinition, yaml.YAMLObject):
    """
        A group of other definitions to pull source files from
    """

    yaml_tag = '!tnndata/group';

    contents: list[InputDefinition] = [];
    """Input definitions contained within this group"""

    def get_files(self) -> list[InputFiles]:
        return functools.reduce(lambda a, b: a + b, [ child.get_files() for child in self.contents ]);


class FileDefinition(InputDefinitionWithData, yaml.YAMLObject):
    """
        A file or directory to pull data from
    """

    yaml_tag = '!tnndata/file';

    path: Path;
    """The path to the target file or directory"""

    # this could surely be optimized
    def get_files(self) -> list[InputFiles]:
        root = Path(self.path); # We have to cast the path to a Path because we don't know what
                                # PyYAML will give us. Thanks PyYAML. I'll fix it with the custom
                                # loader.

        if not root.exists():
            raise FileNotFoundError(f"File/Directory \"{root}\" does not exist");

        paths = [];
        if root.is_dir():
            for dirpath, dirname, filenames in root.walk():
                for filename in filenames:
                    file         = dirpath/filename;
                    _, _, ext_ok = get_ext(file.name, I3FILE_EXTENSIONS);

                    if file.is_dir() or not ext_ok:
                        continue;

                    paths.append(dirpath/file);
        else:
            paths.append(root)

        files          = InputFiles();
        files.files    = paths;
        files.resource = InputResourceType(self.resource);
        files.layout   = str(self.layout);
        return [files];

def read_input_definition(path: Path) -> InputDefinition:
    """
        Load an input definition from a file

        THIS FUNCTION IS NOT SAFE. DO NOT RUN THIS FUNCTION ON UNKNOWN DATA!!!
    """

    # TODO: This is very WIP. In the future I would like to use a custom Loader
    #       solution, because PyYAML's Loader isn't that great and is very verbose...
    data = yaml.load(open(path), yaml.Loader);

    if not isinstance(data, InputDefinition):
        raise Exception("Input definition file \"{path}\" does not deserialize to a InputDefinition");

    return data;
