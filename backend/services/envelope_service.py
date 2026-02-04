from __future__ import annotations

import os
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.config.app_config import settings


class EnvelopeService:
    def __init__(self):
        self.envelopes: Dict[str, Dict] = {}
        self.static_dir = settings.static_files_dir
        self.envelopes_dir = settings.envelopes_dir

    async def generate_envelope(
        self,
        x_axis: str,
        y_axis: str,
        x_data: List[float],
        y_data: List[float],
        x_label: str,
        y_label: str,
        title: str,
        show_grid: bool = True,
        show_legend: bool = True,
    ) -> Dict[str, Any]:
        """生成包络图"""
        envelope_id = str(uuid.uuid4())

        envelope_data = {
            'envelope_id': envelope_id,
            'x_axis': x_axis,
            'y_axis': y_axis,
            'x_data': x_data,
            'y_data': y_data,
            'x_label': x_label,
            'y_label': y_label,
            'title': title,
            'show_grid': show_grid,
            'show_legend': show_legend,
            'created_at': datetime.now().isoformat(),
        }

        self.envelopes[envelope_id] = envelope_data

        os.makedirs(self.envelopes_dir, exist_ok=True)
        envelope_file = os.path.join(self.envelopes_dir, f'{envelope_id}.json')
        with open(envelope_file, 'w') as f:
            json.dump(envelope_data, f, indent=2)

        plotly_code = self._generate_plotly_code(envelope_data)

        return {
            'envelope_id': envelope_id,
            'plotly_code': plotly_code,
            'plotly_data': envelope_data,
        }

    def _generate_plotly_code(self, envelope_data: Dict[str, Any]) -> str:
        """生成Plotly.js代码"""
        import plotly.graph_objects as go
        import plotly.express as px

        x_data = envelope_data['x_data']
        y_data = envelope_data['y_data']
        x_axis = envelope_data['x_axis']
        y_axis = envelope_data['y_axis']
        x_label = envelope_data['x_label']
        y_label = envelope_data['y_label']
        title = envelope_data['title']
        show_grid = envelope_data.get('show_grid', True)
        show_legend = envelope_data.get('show_legend', True)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            name='Constraint Envelope',
            line=dict(color='blue', width=2),
            marker=dict(size=8, color='blue'),
        ))

        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            showgrid=show_grid,
            showlegend=show_legend,
            hovermode='closest',
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
            ),
        )

        return fig.to_html(include_plotlyjs='cdn')

    def get_envelope_data(self, envelope_id: str) -> Optional[Dict[str, Any]]:
        """获取包络图数据"""
        return self.envelopes.get(envelope_id)

    def delete_envelope(self, envelope_id: str) -> bool:
        """删除包络图"""
        if envelope_id not in self.envelopes:
            return False

        del self.envelopes[envelope_id]

        envelope_file = os.path.join(self.envelopes_dir, f'{envelope_id}.json')
        if os.path.exists(envelope_file):
            os.remove(envelope_file)

        return True

    def list_envelopes(self) -> Dict[str, Dict[str, Any]]:
        """列出所有包络图"""
        return self.envelopes

    async def create_preset_envelope(self) -> Dict[str, Any]:
        """创建预设包络图"""
        envelope_id = str(uuid.uuid4())

        preset_data = {
            'envelope_id': envelope_id,
            'x_axis': 'w_s',
            'y_axis': 't_w',
            'x_data': [100, 150, 200, 250, 300],
            'y_data': [0.25, 0.30, 0.35, 0.40, 0.45],
            'x_label': 'Wing Loading (N/m²)',
            'y_label': 'Thrust-to-Weight Ratio',
            'title': 'Preset Constraint Envelope',
            'show_grid': True,
            'show_legend': True,
            'is_preset': True,
            'created_at': datetime.now().isoformat(),
        }

        self.envelopes[envelope_id] = preset_data

        os.makedirs(self.envelopes_dir, exist_ok=True)
        envelope_file = os.path.join(self.envelopes_dir, f'{envelope_id}.json')
        with open(envelope_file, 'w') as f:
            json.dump(preset_data, f, indent=2)

        plotly_code = self._generate_plotly_code(preset_data)

        return {
            'envelope_id': envelope_id,
            'plotly_code': plotly_code,
            'plotly_data': preset_data,
        }

    def list_preset_envelopes(self) -> List[Dict[str, Any]]:
        """列出预设包络图"""
        return [
            envelope_data
            for envelope_data in self.envelopes.values()
            if envelope_data.get('is_preset', False)
        ]

    def export_envelope(self, envelope_id: str, format: str = "png") -> Dict[str, Any]:
        """导出包络图"""
        envelope_data = self.get_envelope_data(envelope_id)
        if not envelope_data:
            raise ValueError(f"Envelope {envelope_id} not found")

        if format == 'png':
            return self._export_png(envelope_id, envelope_data)
        elif format == 'svg':
            return self._export_svg(envelope_id, envelope_data)
        elif format == 'html':
            return self._export_html(envelope_id, envelope_data)
        elif format == 'json':
            return self._export_json(envelope_id, envelope_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_png(self, envelope_id: str, envelope_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出为PNG"""
        import kaleido

        plotly_code = self._generate_plotly_code(envelope_data)

        output_file = os.path.join(self.envelopes_dir, f'{envelope_id}.png')
        kaleido.plot(plotly_code, output=output_file, engine='kaleido-scatter')

        url = f'/static/envelopes/{envelope_id}.png'

        return {
            'url': url,
            'format': 'png',
        }

    def _export_svg(self, envelope_id: str, envelope_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出为SVG"""
        import kaleido

        plotly_code = self._generate_plotly_code(envelope_data)

        output_file = os.path.join(self.envelopes_dir, f'{envelope_id}.svg')
        kaleido.plot(plotly_code, output=output_file, engine='kaleido-scatter')

        url = f'/static/envelopes/{envelope_id}.svg'

        return {
            'url': url,
            'format': 'svg',
        }

    def _export_html(self, envelope_id: str, envelope_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出为HTML"""
        plotly_code = self._generate_plotly_code(envelope_data)

        output_file = os.path.join(self.envelopes_dir, f'{envelope_id}.html')
        with open(output_file, 'w') as f:
            f.write(plotly_code)

        url = f'/static/envelopes/{envelope_id}.html'

        return {
            'url': url,
            'format': 'html',
        }

    def _export_json(self, envelope_id: str, envelope_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出为JSON"""
        output_file = os.path.join(self.envelopes_dir, f'{envelope_id}.json')
        with open(output_file, 'w') as f:
            json.dump(envelope_data, f, indent=2)

        url = f'/static/envelopes/{envelope_id}.json'

        return {
            'url': url,
            'format': 'json',
        }


global_envelope_service = EnvelopeService()
