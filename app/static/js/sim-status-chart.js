// SIM Status Distribution Donut Chart using D3.js
(function() {
    'use strict';

    const width = 400;
    const height = 400;
    const radius = Math.min(width, height) / 2 - 40;

    // Color scheme for different statuses - Deutsche Telekom inspired with semantic colors
    const colorScale = d3.scaleOrdinal()
        .domain(['active', 'inactive', 'suspended', 'available', 'unknown', 'provisioning'])
        .range(['#00b8a9', '#6b6b6b', '#ff9500', '#e20074', '#9b9b9b', '#3498db']);

    // Create SVG container
    const svg = d3.select('#sim-status-chart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${width / 2}, ${height / 2})`);

    // Create tooltip
    const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('opacity', 0);

    // Arc generator for donut chart
    const arc = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius);

    // Arc generator for hover effect
    const arcHover = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius * 1.1);

    // Pie layout
    const pie = d3.pie()
        .value(d => d.count)
        .sort(null);

    // Fetch data and render chart
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

            // Calculate total for percentage
            const total = d3.sum(data, d => d.count);

            // Create arcs
            const arcs = svg.selectAll('.arc')
                .data(pie(data))
                .enter()
                .append('g')
                .attr('class', 'arc');

            // Draw paths
            arcs.append('path')
                .attr('d', arc)
                .attr('fill', d => colorScale(d.data.status))
                .attr('stroke', 'white')
                .attr('stroke-width', 2)
                .style('cursor', 'pointer')
                .on('mouseenter', function(event, d) {
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .attr('d', arcHover);

                    const percentage = ((d.data.count / total) * 100).toFixed(1);
                    tooltip.transition()
                        .duration(200)
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
                        .duration(200)
                        .attr('d', arc);

                    tooltip.transition()
                        .duration(500)
                        .style('opacity', 0);
                })
                .transition()
                .duration(1000)
                .attrTween('d', function(d) {
                    const interpolate = d3.interpolate({startAngle: 0, endAngle: 0}, d);
                    return function(t) {
                        return arc(interpolate(t));
                    };
                });

            // Add center text showing total
            svg.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '-0.5em')
                .style('font-size', '32px')
                .style('font-weight', 'bold')
                .style('fill', '#262626')
                .text(total);

            svg.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '1.5em')
                .style('font-size', '14px')
                .style('fill', '#6b6b6b')
                .text('Total SIMs');

            // Create legend
            const legend = d3.select('#chart-legend')
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
        })
        .catch(error => {
            console.error('Error fetching SIM status data:', error);
            d3.select('#sim-status-chart')
                .append('p')
                .attr('class', 'error-message')
                .text('Error loading chart data');
        });
})();
