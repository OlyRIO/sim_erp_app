// SIM Carrier Distribution Horizontal Bar Chart using D3.js
(function() {
    'use strict';

    const carrierColors = {
        'Hrvatski Telekom': '#e20074',
        'A1 Hrvatska': '#c40f39',
        'Telemach Hrvatska': '#00b8a9',
        'Unknown': '#9b9b9b'
    };

    const chartRoot = document.getElementById('carrier-chart');
    const svg = d3.select(chartRoot).append('svg');
    const plotGroup = svg.append('g');

    const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('opacity', 0);

    let chartData = null;

    const renderChart = () => {
        if (!chartData || chartData.length === 0) return;

        const bounds = chartRoot.getBoundingClientRect();
        const fullWidth = Math.max(220, bounds.width || chartRoot.parentElement?.getBoundingClientRect().width || 320);

        const leftMargin = Math.max(100, Math.min(160, fullWidth * 0.32));
        const margin = {top: 20, right: 16, bottom: 40, left: leftMargin};

        const innerWidth = Math.max(140, fullWidth - margin.left - margin.right);
        const innerHeight = Math.max(chartData.length * 42, 200);

        svg
            .attr('width', fullWidth)
            .attr('height', innerHeight + margin.top + margin.bottom);

        plotGroup.attr('transform', `translate(${margin.left},${margin.top})`);
        plotGroup.selectAll('*').remove();

        const xScale = d3.scaleLinear()
            .domain([0, d3.max(chartData, d => d.count) || 0])
            .nice()
            .range([0, innerWidth]);

        const yScale = d3.scaleBand()
            .domain(chartData.map(d => d.carrier))
            .range([0, innerHeight])
            .padding(0.25);

        plotGroup.append('g')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(d3.axisBottom(xScale).ticks(4))
            .style('font-size', '12px');

        plotGroup.append('g')
            .call(d3.axisLeft(yScale))
            .style('font-size', '13px')
            .style('font-weight', '500');

        const total = d3.sum(chartData, d => d.count);

        plotGroup.selectAll('.bar')
            .data(chartData)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', 0)
            .attr('y', d => yScale(d.carrier))
            .attr('height', yScale.bandwidth())
            .attr('fill', d => carrierColors[d.carrier] || carrierColors['Unknown'])
            .attr('rx', 4)
            .style('cursor', 'pointer')
            .on('mouseenter', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(150)
                    .attr('opacity', 0.85);

                const percentage = total ? ((d.count / total) * 100).toFixed(1) : '0.0';
                tooltip.transition()
                    .duration(150)
                    .style('opacity', 0.95);
                tooltip.html(`
                    <strong>${d.carrier}</strong><br/>
                    SIMs: ${d.count}<br/>
                    Share: ${percentage}%
                `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseleave', function() {
                d3.select(this)
                    .transition()
                    .duration(150)
                    .attr('opacity', 1);

                tooltip.transition()
                    .duration(250)
                    .style('opacity', 0);
            })
            .attr('width', d => xScale(d.count));

        plotGroup.selectAll('.bar-label')
            .data(chartData)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => xScale(d.count) + 6)
            .attr('y', d => yScale(d.carrier) + yScale.bandwidth() / 2)
            .attr('dy', '0.35em')
            .style('font-size', '13px')
            .style('font-weight', 'bold')
            .style('fill', '#262626')
            .text(d => d.count);

        plotGroup.append('text')
            .attr('x', innerWidth / 2)
            .attr('y', -6)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#6b6b6b')
            .text(`Total: ${total} SIMs across ${chartData.length} carriers`);
    };

    fetch('/api/sim-carrier-distribution')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                d3.select('#carrier-chart')
                    .append('p')
                    .attr('class', 'no-data-message')
                    .text('No carrier data available');
                return;
            }

            chartData = data;
            renderChart();

            if (window.ResizeObserver) {
                const resizeObserver = new ResizeObserver(renderChart);
                resizeObserver.observe(chartRoot);
            } else {
                window.addEventListener('resize', renderChart);
            }
        })
        .catch(error => {
            console.error('Error fetching carrier data:', error);
            d3.select('#carrier-chart')
                .append('p')
                .attr('class', 'error-message')
                .text('Error loading chart data');
        });
})();
