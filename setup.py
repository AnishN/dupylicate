from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy as np
import os
import platform

libraries = {
    "Linux": ["avutil", "avformat", "avcodec", "swscale"],
    "Windows": [],
}
language = "c"
#args = ["-w", "-std=c11", "-O3", "-ffast-math", "-march=native", "-fopenmp"]
#link_args = ["-fopenmp"]
args = ["-w", "-std=c11", "-O3", "-ffast-math", "-march=native"]
link_args = []

include_dirs = [np.get_include(), "./dupe_finder/libs/include"]
library_dirs = ["./dupe_finder/libs/shared"]
"""
macros = [
    ("CYTHON_TRACE", "1"),
]
"""
macros = []

annotate = True
quiet = False
directives = {
    "binding": True,
    "boundscheck": False,
    "cdivision": True,
    "initializedcheck": False,
    "language_level": "3",
    #"linetrace": True,
    "nonecheck": False,
    #"profile": True,
    "wraparound": False,
}

if __name__ == "__main__":
    system = platform.system()
    libs = libraries[system]
    extensions = []
    ext_modules = []
    
    #create extensions
    for path, dirs, file_names in os.walk("."):
        for file_name in file_names:
            if file_name.endswith("pyx"):
                ext_path = "{0}/{1}".format(path, file_name)
                ext_name = ext_path \
                    .replace("./", "") \
                    .replace("/", ".") \
                    .replace(".pyx", "")
                ext = Extension(
                    name=ext_name, 
                    sources=[ext_path], 
                    libraries=libs,
                    language=language,
                    extra_compile_args=args,
                    extra_link_args=link_args,
                    include_dirs=include_dirs,
                    library_dirs=library_dirs,
                    runtime_library_dirs=library_dirs,
                    define_macros=macros,
                )
                extensions.append(ext)
    
    #setup all extensions
    ext_modules = cythonize(
        extensions, 
        annotate=annotate, 
        compiler_directives=directives,
        quiet=quiet
    )
    
    #setup all data files
    data_files = {}
    """
    for path, dirs, file_names in os.walk("./resources"):
        if file_names != []:
            data_files[path] = file_names
    """

    setup(
        name="pyorama",
        description="A performant game engine written in cython.",
        version="0.0.2",
        license="MIT",
        url="https://github.com/AnishN/pyorama",
        project_urls={
            "Source Code": "https://github.com/AnishN/pyorama",
        },
        #download_url="https://github.com/AnishN/pyorama/archive/v0.0.2.tar.gz",
        author="Anish Narayanan",
        author_email="anish.narayanan32@gmail.com",
        install_requires=["cython", "numpy", "setuptools"],
        packages=find_packages(),
        package_data=data_files,
        keywords=["game", "2D", "3D", "rendering", "cython", "performance"],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Topic :: Games/Entertainment",
            "Topic :: Multimedia :: Graphics :: 3D Rendering",
            "Topic :: Multimedia :: Graphics",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
        ],
        ext_modules=ext_modules,
    )
