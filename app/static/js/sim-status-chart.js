// SIM Status Distribution Donut Chart using D3.js
(function() {
    'use strict';

    const colorScale = d3.scaleOrdinal()
        .domain(['active', 'inactive', 'suspended', 'available', 'unknown', 'provisioning'])
        .range(['#00b8a9', '#6b6b6b', '#ff9500', '#e20074', '#9b9b9b', '#3498db']);

    const chartRoot = document.getElementById('sim-status-chart');
    const svg = d3.select(chartRoot).append('svg');
    const plotGroup = svg.append('g');

    const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('opacity', 0);

    const pie = d3.pie()
        .value(d => d.count)
        .sort(null);

    let chartData = null;

    const renderChart = () => {
        if (!chartData || chartData.length === 0) return;

        const bounds = chartRoot.getBoundingClientRect();
        const size = Math.max(240, Math.min(bounds.width || 320, 520));
        const radius = size / 2 - 24;

        svg.attr('width', size).attr('height', size);
        plotGroup.attr('transform', `translate(${size / 2}, ${size / 2})`);

        const arc = d3.arc()
            .innerRadius(radius * 0.6)
            .outerRadius(radius);

        const arcHover = d3.arc()
            .innerRadius(radius * 0.6)
            .outerRadius(radius * 1.1);

        plotGroup.selectAll('*').remove();

        const total = d3.sum(chartData, d => d.count);

        const arcs = plotGroup.selectAll('.arc')
            .data(pie(chartData))
            .enter()
            .append('g')
            .attr('class', 'arc');

        arcs.append('path')
            .attr('d', arc)
            .attr('fill', d => colorScale(d.data.status))
            .attr('stroke', 'white')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('mouseenter', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(150)
                    .attr('d', arcHover);

                const percentage = ((d.data.count / total) * 100).toFixed(1);
                tooltip.transition()
                    .duration(150)
                    .style('opacity', 0.95);
                tooltip.html(`
                    <strong>${d.data.status}</strong><br/>
                    Count: ${d.data.count}<br/>
                    Percentage: ${percentage}%
                `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseleave', function() {
                d3.select(this)
                    .transition()
                    .duration(150)
                    .attr('d', arc);

                tooltip.transition()
                    .duration(250)
                    .style('opacity', 0);
            });

        plotGroup.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '-0.5em')
            .style('font-size', '32px')
            .style('font-weight', 'bold')
            .style('fill', '#262626')
            .text(total);

        plotGroup.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '1.5em')
            .style('font-size', '14px')
            .style('fill', '#6b6b6b')
            .text('Total SIMs');
    };

    fetch('/api/sim-status-distribution')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                d3.select('#sim-status-chart')
                    .append('p')
                    .attr('class', 'no-data-message')
                    .text('No SIM data available');
                return;
            }

            chartData = data;

            const legendRoot = d3.select('#chart-legend');
            legendRoot.selectAll('*').remove();

            const legend = legendRoot
                .selectAll('.legend-item')
                .data(data)
                .enter()
                .append('div')
                .attr('class', 'legend-item');

            legend.append('div')
                .attr('class', 'legend-color')
                .style('background-color', d => colorScale(d.status));

            legend.append('span')
                .text(d => `${d.status}: ${d.count}`);

            renderChart();

            if (window.ResizeObserver) {
                const resizeObserver = new ResizeObserver(renderChart);
                resizeObserver.observe(chartRoot);
            } else {
                window.addEventListener('resize', renderChart);
            }
        })
        .catch(error => {
            console.error('Error fetching SIM status data:', error);
            d3.select('#sim-status-chart')
                .append('p')
                .attr('class', 'error-message')
                .text('Error loading chart data');
        });
})();
