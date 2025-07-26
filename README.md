# Framework for benchmarking Automatic Program Repair tools

Nexus connects APR tools with benchmarks and orchestrates the repair workflow through a scripted interaction.

If you use Nexus in academic context, please cite:
```bibtex
@article{Pinconschi2022MaestroAP,
  title={Maestro: a platform for benchmarking automatic program repair tools on software vulnerabilities},
  author={Eduard Pinconschi and Quang-Cuong Bui and Rui Abreu and Pedro Ad{\~a}o and Riccardo Scandariato},
  journal={Proceedings of the 31st ACM SIGSOFT International Symposium on Software Testing and Analysis},
  year={2022},
  url={https://api.semanticscholar.org/CorpusID:250562496}
}
```

## Installation

```
$ pip install -r requirements.txt

$ pip install setup.py
```

## Development

This project includes a number of helpers in the `Makefile` to streamline common development tasks.

### Environment Setup

The following demonstrates setting up and working with a development environment:

```
### create a virtualenv for development

$ make virtualenv

$ source env/bin/activate


### run nexus cli application

$ nexus --help


### run pytest / coverage

$ make test
```

