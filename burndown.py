import numpy
from matplotlib import pyplot


def burndown(x, y_committed, y_interrupt):
    fig = pyplot.figure()
    ax1 = fig.add_subplot(111)

    stack = numpy.row_stack((y_committed, y_interrupt))
    stacked_interrupt = numpy.cumsum(stack, axis=0)

    ax1.fill_between(x, 0, y_committed)
    ax1.fill_between(x, y_committed, stacked_interrupt[1, :])
    ax1.plot([max(x), min(x)], [max(y_committed), 0], ':', color="#800020", lw=2)
    ax1.bar(x, y_interrupt)

    ax = fig.gca()
    ax.set_xlim(ax.get_xlim()[::-1])
    ax1.grid(color='#D3D3D3', linestyle=':', linewidth=1)

    pyplot.show()


def main():
    x = numpy.arange(10, -1, -1)
    y_committed = [70, 68, 68, 64, 55, 49, 41, 40, 32, 22, 19]
    y_interrupt = [0, 8, 12, 8, 6, 12, 8, 4, 2, 6, 4]

    burndown(x, y_committed, y_interrupt)


if __name__ == "__main__":
    main()
